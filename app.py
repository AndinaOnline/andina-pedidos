"""
Andina — Sistema de Pedidos
Main Streamlit application
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import json, os

from styles import CSS, COLORS, render_header, section_title
from data_engine import (
    load_orders, load_inventory, load_costs, merge_orders,
    build_analysis_df, get_historical_monthly, yoy_for_month, KNOWN_PROVS
)
from pdf_generator import generate_pdf

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
_icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'andina_logo.png')
st.set_page_config(
    page_title="Andina — Pedidos",
    page_icon=_icon_path if os.path.exists(_icon_path) else None,
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(CSS, unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
def init_state():
    # Histórico grabado: se carga siempre desde el archivo del repo.
    base_orders = None
    base_path = os.path.join(os.path.dirname(__file__), 'ventas_historico.csv')
    if os.path.exists(base_path):
        try:
            base_orders = pd.read_csv(base_path, parse_dates=['fecha'])
        except Exception:
            base_orders = None
    defaults = {
        'orders_df': base_orders,
        'inv_df': None,
        'costs_df': None,
        'analysis_df': None,
        'mes_actual_fc': None,   # estimado mes en curso (None = sin definir)
        'mes_prox_fc': None,     # estimado mes próximo
        'forecast_anual': {},    # {mes:int} plan anual
        'prov_mix_override': {},
        'edited_pedido': {},     # {sku: qty} user edits
        'edited_costs': {},      # {sku: new_cost} cost overrides
        'active_tab': 0,
        'prov_params': {p: {'lt': 2, 'cob': 6} for p in KNOWN_PROVS},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ── PERSISTENCIA DEL PLAN ANUAL (sobrevive entre sesiones del deploy) ──────────
_PLAN_PATH = os.path.join(os.path.dirname(__file__), 'forecast_plan.json')
def _load_plan():
    try:
        with open(_PLAN_PATH, encoding='utf-8') as f:
            return {int(k): int(v) for k, v in json.load(f).items()}
    except Exception:
        return {}
def _save_plan(plan):
    try:
        with open(_PLAN_PATH, 'w', encoding='utf-8') as f:
            json.dump({str(k): int(v) for k, v in plan.items()}, f)
    except Exception:
        pass
if not st.session_state.get('forecast_anual'):
    st.session_state['forecast_anual'] = _load_plan()

# ── HEADER ────────────────────────────────────────────────────────────────────
render_header(f"Sistema de Pedidos · {datetime.now().strftime('%d/%m/%Y')}")

# ── TABS ──────────────────────────────────────────────────────────────────────
tabs = st.tabs(["Inicio", "Análisis", "Pedidos", "Recomendaciones"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 0 — INICIO
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    section_title("Actualizar datos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<p style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#606060;">Productos WooCommerce (CSV)</p>', unsafe_allow_html=True)
        inv_file = st.file_uploader("Productos", type=['csv','xlsx'], label_visibility="collapsed", key="inv_upload")
        if inv_file:
            st.session_state['inv_df'] = load_inventory(inv_file)
            st.markdown('<div class="upload-ok">Inventario cargado</div>', unsafe_allow_html=True)
        elif st.session_state['inv_df'] is not None:
            st.markdown('<div class="upload-ok">Inventario en memoria</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="upload-pending">Subí el export de WooCommerce (Productos → Exportar)</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<p style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#606060;">Ventas del mes (XLSX)</p>', unsafe_allow_html=True)
        ord_file = st.file_uploader("Ventas", type=['xlsx','csv'], label_visibility="collapsed", key="ord_upload")
        if ord_file:
            new_orders = load_orders(ord_file)
            st.session_state['orders_df'] = merge_orders(st.session_state['orders_df'], new_orders)
            st.session_state['analysis_df'] = None
            st.markdown(f'<div class="upload-ok">{len(new_orders)} lineas cargadas · histórico actualizado</div>', unsafe_allow_html=True)
        elif st.session_state['orders_df'] is not None:
            st.markdown(f'<div class="upload-ok">Histórico cargado ({len(st.session_state["orders_df"])} lineas)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="upload-pending">Subí el export de pedidos de WooCommerce</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<p style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#606060;">Costos proveedoras (XLSX)</p>', unsafe_allow_html=True)
        cost_file = st.file_uploader("Costos", type=['xlsx','csv'], label_visibility="collapsed", key="cost_upload")
        if cost_file:
            st.session_state['costs_df'] = load_costs(cost_file)
            st.session_state['analysis_df'] = None
            st.markdown(f'<div class="upload-ok">{len(st.session_state["costs_df"])} SKUs con costo</div>', unsafe_allow_html=True)
        elif st.session_state['costs_df'] is not None:
            st.markdown(f'<div class="upload-ok">Costos en memoria ({len(st.session_state["costs_df"])} SKUs)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="upload-pending">Subí el archivo de costos de proveedoras</div>', unsafe_allow_html=True)
    
    all_loaded = all([st.session_state['orders_df'] is not None,
                      st.session_state['inv_df'] is not None,
                      st.session_state['costs_df'] is not None])
    
    # ── HISTORIAL DE VENTAS ────────────────────────────────────────────────────
    if st.session_state['orders_df'] is not None:
        st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)
        section_title("Ventas históricas — últimos 6 meses")
        
        hist = get_historical_monthly(st.session_state['orders_df'].copy())
        today = datetime.now()
        
        months_show = []
        for offset in range(5, -1, -1):
            yr = today.year if today.month - offset > 0 else today.year - 1
            mo = (today.month - offset - 1) % 12 + 1
            months_show.append((yr, mo))
        
        month_names = {1:'Ene',2:'Feb',3:'Mar',4:'Abr',5:'May',6:'Jun',
                       7:'Jul',8:'Ago',9:'Sep',10:'Oct',11:'Nov',12:'Dic'}
        
        # Chart — grouped bars 2025 vs 2026
        labels = [f"{month_names[m]}" for y, m in months_show]
        vals_2025 = [int(hist[(hist['year']==y-1)&(hist['month']==m)]['units'].sum()) for y, m in months_show]
        vals_curr = [int(hist[(hist['year']==y)&(hist['month']==m)]['units'].sum()) for y, m in months_show]
        
        fig = go.Figure()
        fig.add_bar(name=f'{months_show[0][0]-1}', x=labels, y=vals_2025,
                    marker_color=COLORS['arena'], opacity=0.7)
        fig.add_bar(name=f'{months_show[0][0]}', x=labels, y=vals_curr,
                    marker_color='#606060')
        fig.update_layout(
            barmode='group', height=200, margin=dict(l=0,r=0,t=10,b=0),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation='h', y=1.1, x=0),
            yaxis=dict(gridcolor=COLORS['arena'], gridwidth=0.5),
            xaxis=dict(gridcolor='rgba(0,0,0,0)'),
            font=dict(family='Raleway', size=11, color=COLORS['gris_texto']),
        )
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        # YoY summary row
        cols_h = st.columns(len(months_show))
        for i, (yr, mo) in enumerate(months_show):
            v_curr = vals_curr[i]; v_prev = vals_2025[i]
            yoy = (v_curr/v_prev - 1) * 100 if v_prev > 0 and v_curr > 0 else None
            with cols_h[i]:
                yoy_str = f"{yoy:+.0f}% YoY" if yoy is not None else "—"
                color = "#155724" if (yoy or 0) >= 0 else "#721c24"
                st.markdown(f"""
                <div style="text-align:center; font-family:'Raleway',sans-serif;">
                  <div style="font-size:10px; color:{COLORS['gris_texto']}; text-transform:uppercase; letter-spacing:0.5px;">{month_names[mo]}</div>
                  <div style="font-size:16px; font-weight:700; color:{COLORS['oscuro']};">{v_curr}u</div>
                  <div style="font-size:11px; color:{COLORS['gris_texto']};">{months_show[0][0]-1}: {v_prev}u</div>
                  <div style="font-size:10px; color:{color};">{yoy_str}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Totals line
        ytd_curr = sum(vals_curr)
        ytd_prev = sum(vals_2025)
        ytd_yoy = (ytd_curr/ytd_prev - 1)*100 if ytd_prev > 0 else 0
        prom = ytd_curr / len(months_show) if months_show else 0
        st.markdown(f"""
        <div style="border-top:0.5px solid {COLORS['arena']}; margin:10px 0; padding:10px 0;
                    display:flex; gap:32px; font-family:'Raleway',sans-serif; font-size:12px; color:{COLORS['gris_texto']};">
          <span>Acumulado {months_show[-1][0]}: <strong style="color:{COLORS['negro']};">{ytd_curr}u</strong></span>
          <span>vs {months_show[-1][0]-1}: <strong style="color:{COLORS['negro']};">{ytd_prev}u</strong></span>
          <span style="color:#155724; font-weight:600;">{ytd_yoy:+.0f}% YTD</span>
          <span style="margin-left:auto;">Prom mensual: <strong>{prom:.0f}u</strong></span>
        </div>
        """, unsafe_allow_html=True)
    
    # ── PLAN DE VENTAS DEL AÑO (carga única) ─────────────────────────────────
    st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
    section_title("Plan de ventas del año — carga única")

    today = datetime.now()
    month_names_full = {1:'Enero',2:'Febrero',3:'Marzo',4:'Abril',5:'Mayo',6:'Junio',
                        7:'Julio',8:'Agosto',9:'Septiembre',10:'Octubre',11:'Noviembre',12:'Diciembre'}
    mes_abbr = {1:'Ene',2:'Feb',3:'Mar',4:'Abr',5:'May',6:'Jun',7:'Jul',8:'Ago',9:'Sep',10:'Oct',11:'Nov',12:'Dic'}

    hist_data = get_historical_monthly(st.session_state['orders_df'].copy()) if st.session_state['orders_df'] is not None else pd.DataFrame()

    def _u(year, month):
        if hist_data.empty: return 0
        return int(hist_data[(hist_data['year']==year)&(hist_data['month']==month)]['units'].sum())

    # Tendencia YoY REAL de meses cerrados (ene..mes anterior). Sin datos -> None (no inventa).
    avg_yoy = None
    if not hist_data.empty and today.month > 1:
        cur_sum = sum(_u(today.year, m) for m in range(1, today.month))
        prev_sum = sum(_u(today.year-1, m) for m in range(1, today.month))
        if prev_sum > 0:
            avg_yoy = cur_sum/prev_sum - 1
    yoy_txt = f"{avg_yoy*100:+.0f}%" if avg_yoy is not None else "sin dato"

    def _sugerido(m):
        prev = _u(today.year-1, m)
        if prev > 0 and avg_yoy is not None:
            return int(prev*(1+avg_yoy))
        return prev  # sin tendencia: usa año pasado; sin año pasado: 0 (no inventa)

    # Plan anual: arranca de lo guardado en disco; completa meses faltantes con sugerido.
    plan = st.session_state.get('forecast_anual') or {}
    for m in range(today.month, 13):
        if m not in plan:
            plan[m] = _sugerido(m)
    st.session_state['forecast_anual'] = plan

    if today.month > 1:
        cerrados = " · ".join(f"{mes_abbr[m]}: {_u(today.year,m)}u" for m in range(1, today.month))
        st.markdown(f'<div style="font-size:11px;color:{COLORS["gris_texto"]};font-family:Raleway;margin-bottom:8px;">Meses cerrados {today.year} (reales): {cerrados} &nbsp;&middot;&nbsp; Tendencia YoY acumulada: <strong>{yoy_txt}</strong></div>', unsafe_allow_html=True)

    def _crec(val, base):
        return round((val/base - 1)*100, 0) if base > 0 else None

    plan_rows = []
    for m in range(today.month, 13):
        ap = _u(today.year-1, m)
        sug = _sugerido(m)
        pl = int(plan.get(m, sug))
        plan_rows.append({
            'Mes': f"{mes_abbr[m]} {today.year}",
            'Año pasado': ap,
            'Sugerido': sug,
            'Crec. sug.': _crec(sug, ap),
            'Plan': pl,
            'Crec. plan': _crec(pl, ap),
        })
    plan_df = pd.DataFrame(plan_rows)
    edited_plan = st.data_editor(
        plan_df,
        column_config={
            'Mes': st.column_config.TextColumn('Mes', disabled=True),
            'Año pasado': st.column_config.NumberColumn(f'{today.year-1}', disabled=True, format="%d u"),
            'Sugerido': st.column_config.NumberColumn('Sugerido', disabled=True, format="%d u"),
            'Crec. sug.': st.column_config.NumberColumn('Crec. sug.', disabled=True, format="%d%%"),
            'Plan': st.column_config.NumberColumn('Plan (editable)', min_value=0, max_value=5000, step=10, format="%d u"),
            'Crec. plan': st.column_config.NumberColumn('Crec. plan', disabled=True, format="%d%%"),
        },
        hide_index=True, use_container_width=True, key="plan_anual_editor",
    )
    changed = False
    for idx, m in enumerate(range(today.month, 13)):
        try:
            v = int(edited_plan.iloc[idx]['Plan'])
            if plan.get(m) != v:
                changed = True
            plan[m] = v
        except Exception:
            pass
    st.session_state['forecast_anual'] = plan
    if changed:
        _save_plan(plan)   # persiste los ajustes en disco

    st.caption("Cargá el plan una vez al año (se guarda). Cada mes solo subís las ventas: se actualiza el histórico y se recalculan los pedidos.")

    # Totales para el motor: mes en curso y próximo
    mo_next = today.month + 1 if today.month < 12 else 12
    st.session_state['mes_actual_fc'] = int(st.session_state['forecast_anual'].get(today.month, 0))
    st.session_state['mes_prox_fc'] = int(st.session_state['forecast_anual'].get(mo_next, 0))


    # ── METRICS ────────────────────────────────────────────────────────────────
    if all_loaded:
        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
        section_title("Resumen")
        
        if st.session_state['analysis_df'] is None:
            with st.spinner("Calculando análisis..."):
                st.session_state['analysis_df'] = build_analysis_df(
                    inv_df=st.session_state['inv_df'],
                    orders_all=st.session_state['orders_df'],
                    costs_df=st.session_state['costs_df'],
                    prov_params=st.session_state['prov_params'],
                    jun_total=st.session_state['mes_actual_fc'] or 0,
                    jul_total=st.session_state['mes_prox_fc'] or 0,
                    prov_mix_override=st.session_state['prov_mix_override'],
                )
        
        adf = st.session_state['analysis_df']
        activos = adf[adf['Estado'].isin(['Activo','SALE'])]
        quiebres = adf[adf['Alerta'] == 'Quiebre']
        pedidos_propuestos = adf[adf['Pedido_propuesto'] > 0]
        
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("SKUs activos", f"{len(activos)}")
        with m2:
            st.metric("Quiebres de stock", f"{len(quiebres)}", delta=f"-{len(quiebres)} urgentes", delta_color="inverse")
        with m3:
            st.metric("SKUs a pedir", f"{len(pedidos_propuestos)}")
        with m4:
            n_nuevos = adf[adf['Es_nuevo'] & adf['Estado'].isin(['Activo','SALE'])].shape[0]
            st.metric("Productos nuevos", f"{n_nuevos}", delta="<3 meses")
        
        st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)
        if st.button("Recalcular análisis con nuevo forecast", use_container_width=False):
            st.session_state['analysis_df'] = None
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ANÁLISIS
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    if st.session_state['analysis_df'] is None:
        if any(st.session_state[k] is None for k in ['orders_df','inv_df','costs_df']):
            st.info("Subí los tres archivos en la pantalla Inicio para ver el análisis.")
        else:
            with st.spinner("Procesando datos..."):
                st.session_state['analysis_df'] = build_analysis_df(
                    inv_df=st.session_state['inv_df'],
                    orders_all=st.session_state['orders_df'],
                    costs_df=st.session_state['costs_df'],
                    prov_params=st.session_state['prov_params'],
                    jun_total=st.session_state['mes_actual_fc'] or 0,
                    jul_total=st.session_state['mes_prox_fc'] or 0,
                    prov_mix_override=st.session_state['prov_mix_override'],
                )
    
    if st.session_state['analysis_df'] is not None:
        adf = st.session_state['analysis_df']
        
        # ── FILTERS ───────────────────────────────────────────────────────────
        section_title("Filtros")
        f1, f2, f3, f4, f5 = st.columns(5)
        with f1:
            f_rank = st.multiselect("Ranking", ['A','B','C','D'], default=['A','B','C','D'])
        with f2:
            provs_available = sorted({str(p).strip() for p in adf['Proveedor'].dropna().unique() if str(p).strip()})
            f_prov = st.multiselect("Proveedora", provs_available, default=[])
        with f3:
            tipos_available = sorted([t for t in adf['Tipo'].unique() if t])
            f_tipo = st.multiselect("Tipo", tipos_available, default=[])
        with f4:
            estados_available = sorted(adf['Estado'].unique())
            f_estado = st.multiselect("Estado", estados_available, default=['Activo','SALE'])
        with f5:
            f_alerta = st.multiselect("Alerta", ['Quiebre','Urgente','Próximo'], default=[])
        
        # Apply filters
        filtered = adf.copy()
        if f_rank: filtered = filtered[filtered['Prior'].isin(f_rank)]
        if f_prov: filtered = filtered[filtered['Proveedor'].isin(f_prov)]
        if f_tipo: filtered = filtered[filtered['Tipo'].isin(f_tipo)]
        if f_estado: filtered = filtered[filtered['Estado'].isin(f_estado)]
        if f_alerta: filtered = filtered[filtered['Alerta'].isin(f_alerta)]
        
        section_title(f"Resultados — {len(filtered)} productos")
        
        # ── TABLE ─────────────────────────────────────────────────────────────
        # Build display df
        display_cols = ['SKU','Nombre','Tipo','Proveedor','Prior','Estado','Inventario',
                        'Prom_mensual','Cobertura_meses','YTD_2026','Alerta','Pedido_propuesto','Fcst_Jun','Fcst_Jul']
        
        show_df = filtered[display_cols].copy()
        show_df.columns = ['SKU','Nombre','Tipo','Proveedora','Rank.','Estado','Inv.',
                           'Prom/mes','Cob.(m)','YTD 2026','Alerta','Pedido prop.','Fcst mes','Fcst próx']
        show_df['Prom/mes'] = show_df['Prom/mes'].round(1)
        show_df['Cob.(m)'] = show_df['Cob.(m)'].replace(99, '—')
        show_df['Pedido prop.'] = show_df['Pedido prop.'].apply(lambda x: int(x) if x > 0 else '—')
        show_df['Fcst mes'] = show_df['Fcst mes'].round(1)
        show_df['Fcst próx'] = show_df['Fcst próx'].round(1)
        
        # Editable pedido column
        edited = st.data_editor(
            show_df,
            column_config={
                'SKU': st.column_config.TextColumn('SKU', width='small'),
                'Nombre': st.column_config.TextColumn('Nombre', width='medium'),
                'Rank.': st.column_config.TextColumn('Rank.', width='small'),
                'Estado': st.column_config.TextColumn('Estado', width='small'),
                'Inv.': st.column_config.NumberColumn('Inv.', width='small'),
                'Pedido prop.': st.column_config.NumberColumn('Pedido prop.', width='small', min_value=0, max_value=999),
                'Alerta': st.column_config.TextColumn('Alerta', width='small'),
            },
            disabled=[c for c in show_df.columns if c != 'Pedido prop.'],
            use_container_width=True,
            hide_index=True,
            height=500,
        )
        
        # Capture edits
        for i, row in edited.iterrows():
            sku = filtered.loc[i]['SKU']
            orig_qty = filtered.loc[i]['Pedido_propuesto']
            new_qty = row['Pedido prop.']
            if isinstance(new_qty, (int, float)) and new_qty != orig_qty:
                st.session_state['edited_pedido'][sku] = int(new_qty)
        
        st.caption(f"Podés editar la columna 'Pedido prop.' directamente. Los cambios se reflejan en la pestaña Pedidos.")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — PEDIDOS
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[2]:
    if st.session_state['analysis_df'] is None:
        st.info("Completá los datos en Inicio primero.")
    else:
        adf = st.session_state['analysis_df']
        
        # Build pedidos df — products with proposed qty > 0
        pedido_skus = adf[adf['Pedido_propuesto'] > 0].copy()
        
        # Apply user edits
        for sku, qty in st.session_state['edited_pedido'].items():
            pedido_skus.loc[pedido_skus['SKU'] == sku, 'Pedido_propuesto'] = qty
        
        # Provider selector
        section_title("Seleccioná la proveedora")
        provs_with_orders = sorted(pedido_skus[pedido_skus['Proveedor'] != '']['Proveedor'].unique())
        
        if not provs_with_orders:
            st.warning("No hay pedidos propuestos aún. Verificá que los datos estén cargados.")
        else:
            # Pills for provider selection
            prov_cols = st.columns(min(len(provs_with_orders), 6))
            selected_prov = st.session_state.get('selected_prov', provs_with_orders[0])
            
            pills_html = ""
            for p in provs_with_orders:
                active_class = "prov-pill-active" if p == selected_prov else ""
                n_items = len(pedido_skus[pedido_skus['Proveedor'] == p])
                pills_html += f'<span class="prov-pill {active_class}">{p} ({n_items})</span>'
            
            st.markdown(f'<div style="margin-bottom:12px;">{pills_html}</div>', unsafe_allow_html=True)
            
            selected_prov = st.selectbox(
                "Proveedora", provs_with_orders, 
                index=provs_with_orders.index(selected_prov) if selected_prov in provs_with_orders else 0,
                key="prov_selector", label_visibility="collapsed")
            st.session_state['selected_prov'] = selected_prov
            
            # Filter for selected provider
            prov_df = pedido_skus[pedido_skus['Proveedor'] == selected_prov].copy()
            
            section_title(f"Pedido — {selected_prov}")
            
            # Editable table for this provider
            edit_cols = ['SKU','Nombre','SKU_Prov','Nombre_Prov','Pedido_propuesto','Costo_ARS','Imagen_url']
            prov_display = prov_df[edit_cols].copy()
            prov_display.columns = ['SKU','Nombre','SKU Prov.','Descripción Prov.','Cantidad','Precio unit. ARS','URL Foto']
            prov_display['Subtotal ARS'] = prov_display.apply(
                lambda r: int(r['Cantidad'] * r['Precio unit. ARS']) 
                if (pd.notna(r['Precio unit. ARS']) and r['Precio unit. ARS'] > 0) else None, axis=1)
            
            edited_prov = st.data_editor(
                prov_display,
                column_config={
                    'SKU': st.column_config.TextColumn('SKU', width='small'),
                    'Nombre': st.column_config.TextColumn('Nombre', width='medium'),
                    'SKU Prov.': st.column_config.TextColumn('SKU Prov.', width='small'),
                    'Descripción Prov.': st.column_config.TextColumn('Descripción Prov.', width='medium'),
                    'Cantidad': st.column_config.NumberColumn('Cantidad', min_value=0, max_value=999, width='small'),
                    'Precio unit. ARS': st.column_config.NumberColumn('Precio', format="$%d", width='small'),
                    'Subtotal ARS': st.column_config.NumberColumn('Subtotal', format="$%d", disabled=True, width='small'),
                    'URL Foto': st.column_config.LinkColumn('Foto', display_text="Ver", width='small'),
                },
                use_container_width=True,
                hide_index=True,
                key=f"edit_table_{selected_prov}",
            )
            
            # Capture cost edits
            for i, row in edited_prov.iterrows():
                sku = prov_df.loc[i]['SKU']
                new_cost = row['Precio unit. ARS']
                orig_cost = prov_df.loc[i]['Costo_ARS']
                if pd.notna(new_cost) and new_cost != orig_cost:
                    st.session_state['edited_costs'][sku] = new_cost
                new_qty = row['Cantidad']
                st.session_state['edited_pedido'][sku] = int(new_qty) if pd.notna(new_qty) else 0
            
            # Totals
            total_u = edited_prov['Cantidad'].sum()
            total_ars = edited_prov['Subtotal ARS'].dropna().sum()
            
            st.markdown(f"""
            <div style="background:{COLORS['negro']}; color:{COLORS['arena']}; border-radius:8px; 
                        padding:14px 20px; display:flex; justify-content:space-between; 
                        align-items:center; margin:12px 0; font-family:'Raleway';">
              <div>
                <div style="font-size:11px; opacity:0.7; text-transform:uppercase; letter-spacing:1px;">Total pedido — {selected_prov}</div>
                <div style="font-size:12px; opacity:0.6;">{int(total_u)} unidades · {len(edited_prov[edited_prov['Cantidad']>0])} SKUs</div>
              </div>
              <div style="font-size:22px; font-weight:600;">${int(total_ars):,} ARS</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Cost update notice
            if st.session_state['edited_costs']:
                n_updated = len(st.session_state['edited_costs'])
                st.success(f"{n_updated} precio(s) actualizado(s) en esta sesión. Se usarán en el PDF y en rentabilidad.")
            
            # Actions
            col_a, col_b, col_c = st.columns([1,1,3])
            with col_a:
                if st.button("Descargar PDF", use_container_width=True, type="primary"):
                    edited_qtys = {prov_df.iloc[i]['SKU']: int(edited_prov.iloc[i]['Cantidad']) 
                                   for i in range(len(edited_prov))}
                    pdf_bytes = generate_pdf(prov_df, selected_prov, edited_qtys)
                    st.download_button(
                        label="Descargar PDF",
                        data=pdf_bytes,
                        file_name=f"Andina_Pedido_{selected_prov}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
            with col_b:
                if st.button("Copiar para WhatsApp", use_container_width=True):
                    lines = [f"*Pedido Andina — {selected_prov}*", f"Fecha: {datetime.now().strftime('%d/%m/%Y')}", ""]
                    for _, row in edited_prov[edited_prov['Cantidad'] > 0].iterrows():
                        lines.append(f"• {row['SKU']} | {row['Nombre']} | x{int(row['Cantidad'])}" +
                                    (f" | ${int(row['Precio unit. ARS']):,}" if pd.notna(row['Precio unit. ARS']) else ""))
                    lines.append(f"\n*Total: {int(total_u)} uds | ${int(total_ars):,} ARS*")
                    wa_text = "\n".join(lines)
                    st.code(wa_text, language=None)
                    st.caption("Copiá el texto y pegalo en WhatsApp")


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — RECOMENDACIONES
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[3]:
    if st.session_state['analysis_df'] is None:
        st.info("Completá los datos en Inicio primero.")
    else:
        adf = st.session_state['analysis_df']
        
        # Alertas de inventario
        section_title("Alertas de inventario")
        alertas = adf[adf['Alerta'] != ''].sort_values(['Alerta','Prior'])
        
        if len(alertas) == 0:
            st.success("No hay alertas críticas en este momento.")
        else:
            alert_counts = alertas['Alerta'].value_counts()
            ac1, ac2, ac3 = st.columns(3)
            with ac1:
                q = alert_counts.get('Quiebre', 0)
                st.markdown(f'<div style="background:#f8d7da;border-radius:8px;padding:12px;text-align:center;"><div style="font-size:22px;font-weight:600;color:#721c24;">{q}</div><div style="font-size:11px;color:#721c24;">QUIEBRES</div></div>', unsafe_allow_html=True)
            with ac2:
                u = alert_counts.get('Urgente', 0)
                st.markdown(f'<div style="background:#fff3cd;border-radius:8px;padding:12px;text-align:center;"><div style="font-size:22px;font-weight:600;color:#856404;">{u}</div><div style="font-size:11px;color:#856404;">URGENTES</div></div>', unsafe_allow_html=True)
            with ac3:
                p = alert_counts.get('Próximo', 0)
                st.markdown(f'<div style="background:#cce5ff;border-radius:8px;padding:12px;text-align:center;"><div style="font-size:22px;font-weight:600;color:#004085;">{p}</div><div style="font-size:11px;color:#004085;">PRÓXIMOS</div></div>', unsafe_allow_html=True)
            
            st.markdown('<div style="height:10px;"></div>', unsafe_allow_html=True)
            alert_display = alertas[['Alerta','SKU','Nombre','Proveedor','Prior','Estado','Inventario','Prom_mensual','Cobertura_meses']].copy()
            alert_display.columns = ['Alerta','SKU','Nombre','Proveedora','Rank.','Estado','Inv.','Prom/mes','Cob.(m)']
            alert_display['Cob.(m)'] = alert_display['Cob.(m)'].replace(99, '—')
            st.dataframe(alert_display, use_container_width=True, hide_index=True, height=300)
        
        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
        
        # SALE recommendations
        section_title("Candidatos a SALE — C y D con más de 6 meses")
        sale_cand = adf[
            (adf['Prior'].isin(['C','D'])) &
            (adf['Sem_vida'] > 26) &
            (~adf['Estado'].isin(['Borrador','BAJA'])) &
            (adf['Inventario'] > 0)
        ].sort_values(['Prior','Sem_vida'], ascending=[False,False])
        
        if len(sale_cand) > 0:
            st.markdown(f'<div style="font-size:12px;color:{COLORS["gris_texto"]};margin-bottom:8px;">**{len(sale_cand)}** productos candidatos a SALE. Filtrá por proveedora para accionar por lotes.</div>', unsafe_allow_html=True)
            sale_display = sale_cand[['SKU','Nombre','Tipo','Proveedor','Prior','Estado','Inventario','Prom_mensual','Precio_normal','Precio_rebajado']].copy()
            sale_display['Precio recom. (-30%)'] = sale_display['Precio_normal'].apply(
                lambda x: int(x * 0.70) if pd.notna(x) and x > 0 else None)
            sale_display.columns = ['SKU','Nombre','Tipo','Proveedora','Rank.','Estado','Inv.','Prom/mes','Precio normal','Precio rebajado','Precio recom. (-30%)']
            st.dataframe(sale_display, use_container_width=True, hide_index=True, height=300)
        
        st.markdown('<div style="height:8px;"></div>', unsafe_allow_html=True)
        
        # Borrador recommendations
        section_title("Para pasar a Borrador — D, sin stock, aún activos")
        borra_cand = adf[
            (adf['Prior'] == 'D') &
            (adf['Inventario'] == 0) &
            (adf['Estado'].isin(['Activo','SALE'])) &
            (adf['Sem_vida'] > 26)
        ].sort_values('Sem_vida', ascending=False)
        
        if len(borra_cand) > 0:
            st.markdown(f'<div style="font-size:12px;color:{COLORS["gris_texto"]};margin-bottom:8px;">**{len(borra_cand)}** productos sin stock, con ranking D, aún publicados en WooCommerce.</div>', unsafe_allow_html=True)
            borra_display = borra_cand[['SKU','Nombre','Tipo','Proveedor','Estado','Inventario','YTD_2026','Sem_vida']].copy()
            borra_display['Sem_vida'] = borra_display['Sem_vida'].apply(lambda x: f"{x/4.3:.0f} meses")
            borra_display.columns = ['SKU','Nombre','Tipo','Proveedora','Estado','Inv.','YTD 2026','Antigüedad']
            st.dataframe(borra_display, use_container_width=True, hide_index=True, height=250)

