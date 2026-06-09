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
    load_orders, load_inventory, load_costs,
    build_analysis_df, get_historical_monthly, yoy_for_month, KNOWN_PROVS
)
from pdf_generator import generate_pdf

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Andina — Pedidos",
    page_icon="💍",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(CSS, unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        'orders_df': None,
        'inv_df': None,
        'costs_df': None,
        'analysis_df': None,
        'jun_forecast': 380,
        'jul_forecast': 420,
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

# ── HEADER ────────────────────────────────────────────────────────────────────
render_header(f"Sistema de Pedidos · {datetime.now().strftime('%d/%m/%Y')}")

# ── TABS ──────────────────────────────────────────────────────────────────────
tabs = st.tabs(["🏠  Inicio", "📊  Análisis", "📦  Pedidos", "💡  Recomendaciones", "📈  Rentabilidad"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 0 — INICIO
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[0]:
    section_title("Actualizar datos")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<p style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#606060;">📦 Productos WooCommerce (CSV)</p>', unsafe_allow_html=True)
        inv_file = st.file_uploader("Productos", type=['csv','xlsx'], label_visibility="collapsed", key="inv_upload")
        if inv_file:
            st.session_state['inv_df'] = load_inventory(inv_file)
            st.markdown('<div class="upload-ok">✓ Inventario cargado</div>', unsafe_allow_html=True)
        elif st.session_state['inv_df'] is not None:
            st.markdown('<div class="upload-ok">✓ Inventario en memoria</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="upload-pending">Subí el export de WooCommerce (Productos → Exportar)</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<p style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#606060;">🧾 Ventas del mes (XLSX)</p>', unsafe_allow_html=True)
        ord_file = st.file_uploader("Ventas", type=['xlsx','csv'], label_visibility="collapsed", key="ord_upload")
        if ord_file:
            new_orders = load_orders(ord_file)
            if st.session_state['orders_df'] is not None:
                # Merge with existing, deduplicate by date
                combined = pd.concat([st.session_state['orders_df'], new_orders]).drop_duplicates()
                st.session_state['orders_df'] = combined
            else:
                st.session_state['orders_df'] = new_orders
            st.session_state['analysis_df'] = None
            st.markdown(f'<div class="upload-ok">✓ {len(new_orders)} líneas de venta cargadas</div>', unsafe_allow_html=True)
        elif st.session_state['orders_df'] is not None:
            st.markdown(f'<div class="upload-ok">✓ Ventas en memoria ({len(st.session_state["orders_df"])} líneas)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="upload-pending">Subí el export de pedidos de WooCommerce</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<p style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#606060;">💰 Costos proveedoras (XLSX)</p>', unsafe_allow_html=True)
        cost_file = st.file_uploader("Costos", type=['xlsx','csv'], label_visibility="collapsed", key="cost_upload")
        if cost_file:
            st.session_state['costs_df'] = load_costs(cost_file)
            st.session_state['analysis_df'] = None
            st.markdown(f'<div class="upload-ok">✓ {len(st.session_state["costs_df"])} SKUs con costo cargados</div>', unsafe_allow_html=True)
        elif st.session_state['costs_df'] is not None:
            st.markdown(f'<div class="upload-ok">✓ Costos en memoria ({len(st.session_state["costs_df"])} SKUs)</div>', unsafe_allow_html=True)
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
                  <div style="font-size:15px; font-weight:600; color:{COLORS['negro']};">{v_curr}u</div>
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
    
    # ── FORECAST ───────────────────────────────────────────────────────────────
    st.markdown('<div style="height:4px;"></div>', unsafe_allow_html=True)
    section_title("Proyección de ventas — editable")
    
    today = datetime.now()
    month_names_full = {1:'Enero',2:'Febrero',3:'Marzo',4:'Abril',5:'Mayo',6:'Junio',
                        7:'Julio',8:'Agosto',9:'Septiembre',10:'Octubre',11:'Noviembre',12:'Diciembre'}
    
    jun_mo = today.month + 1 if today.month < 12 else 1
    jul_mo = today.month + 2 if today.month < 11 else (today.month + 2) % 12
    jun_yr = today.year if today.month < 12 else today.year + 1
    jul_yr = today.year if today.month < 11 else today.year + (1 if today.month >= 11 else 0)
    
    hist_data = get_historical_monthly(st.session_state['orders_df'].copy()) if st.session_state['orders_df'] is not None else pd.DataFrame()
    
    col_j, col_jl = st.columns(2)
    
    for col, mo, yr, key_fc in [(col_j, jun_mo, jun_yr, 'jun_forecast'), (col_jl, jul_mo, jul_yr, 'jul_forecast')]:
        with col:
            # Reference data
            prev_yr_val = int(hist_data[(hist_data['year']==yr-1)&(hist_data['month']==mo)]['units'].sum()) if not hist_data.empty else 0
            prom_3m = 0
            if not hist_data.empty:
                recent = [int(hist_data[(hist_data['year']==today.year)&(hist_data['month']==m)]['units'].sum())
                          for m in [(today.month-2)%12+1, (today.month-1)%12+1, today.month]]
                prom_3m = int(np.mean(recent))
            
            # Suggested = prev_yr * (1 + avg_yoy)
            avg_ytd_yoy = 0.35  # 35% average growth Ene-May 2026 vs 2025
            suggested = int(prev_yr_val * (1 + avg_ytd_yoy)) if prev_yr_val > 0 else prom_3m
            
            # Pre-fill with suggested if not already set
            if st.session_state[key_fc] in (380, 420):  # defaults
                st.session_state[key_fc] = suggested
            
            st.markdown(f"""
            <div style="background:{COLORS['verde_agua']}; border-radius:10px; padding:14px 16px; border:0.5px solid {COLORS['arena']};">
              <div style="font-size:13px; font-weight:600; font-family:'Raleway'; color:{COLORS['negro']}; margin-bottom:10px;">
                {month_names_full[mo]} {yr}
              </div>
              <div style="display:flex; gap:20px; margin-bottom:12px; padding-bottom:12px; border-bottom:0.5px solid {COLORS['arena']};">
                <div>
                  <div style="font-size:10px; text-transform:uppercase; letter-spacing:0.5px; color:{COLORS['gris_texto']};">{month_names_full[mo]} {yr-1}</div>
                  <div style="font-size:18px; font-weight:500; font-family:Raleway; color:{COLORS['gris_texto']};">{prev_yr_val}u</div>
                </div>
                <div>
                  <div style="font-size:10px; text-transform:uppercase; letter-spacing:0.5px; color:{COLORS['gris_texto']};">Prom últ. 3 meses</div>
                  <div style="font-size:18px; font-weight:500; font-family:Raleway; color:{COLORS['negro']};">{prom_3m}u</div>
                </div>
                <div>
                  <div style="font-size:10px; text-transform:uppercase; letter-spacing:0.5px; color:{COLORS['gris_texto']};">Tend. YoY</div>
                  <div style="font-size:18px; font-weight:500; font-family:Raleway; color:#155724;">+35%</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            
            new_val = st.number_input(
                f"Tu estimado {month_names_full[mo]} (sugerido: {suggested}u)",
                min_value=0, max_value=2000,
                value=st.session_state[key_fc],
                step=10, key=f"input_{key_fc}")
            st.session_state[key_fc] = new_val
            
            # Show comparison
            if prev_yr_val > 0 and new_val > 0:
                pct_vs_prev = (new_val/prev_yr_val - 1)*100
                pct_vs_prom = (new_val/prom_3m - 1)*100 if prom_3m > 0 else 0
                color_p = "#155724" if pct_vs_prev >= 0 else "#721c24"
                st.markdown(f"""
                <div style="font-size:11px; font-family:'Raleway'; color:{COLORS['gris_texto']}; margin-top:4px;">
                  <span style="color:{color_p}; font-weight:500;">{pct_vs_prev:+.0f}%</span> vs {yr-1} · 
                  <span style="color:{color_p}; font-weight:500;">{pct_vs_prom:+.0f}%</span> vs prom mensual
                </div>
                """, unsafe_allow_html=True)
    
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
                    jun_total=st.session_state['jun_forecast'],
                    jul_total=st.session_state['jul_forecast'],
                    prov_mix_override=st.session_state['prov_mix_override'],
                )
        
        adf = st.session_state['analysis_df']
        activos = adf[adf['Estado'].isin(['Activo','SALE'])]
        quiebres = adf[adf['Alerta'] == '🔴 Quiebre']
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
        if st.button("🔄  Recalcular análisis con nuevo forecast", use_container_width=False):
            st.session_state['analysis_df'] = None
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ANÁLISIS
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    if st.session_state['analysis_df'] is None:
        if not all([st.session_state['orders_df'], st.session_state['inv_df'], st.session_state['costs_df']]):
            st.info("Subí los tres archivos en la pantalla Inicio para ver el análisis.")
        else:
            with st.spinner("Procesando datos..."):
                st.session_state['analysis_df'] = build_analysis_df(
                    inv_df=st.session_state['inv_df'],
                    orders_all=st.session_state['orders_df'],
                    costs_df=st.session_state['costs_df'],
                    prov_params=st.session_state['prov_params'],
                    jun_total=st.session_state['jun_forecast'],
                    jul_total=st.session_state['jul_forecast'],
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
            provs_available = sorted([p for p in adf['Proveedor'].unique() if p])
            f_prov = st.multiselect("Proveedora", provs_available, default=[])
        with f3:
            tipos_available = sorted([t for t in adf['Tipo'].unique() if t])
            f_tipo = st.multiselect("Tipo", tipos_available, default=[])
        with f4:
            estados_available = sorted(adf['Estado'].unique())
            f_estado = st.multiselect("Estado", estados_available, default=['Activo','SALE'])
        with f5:
            f_alerta = st.multiselect("Alerta", ['🔴 Quiebre','🟠 Urgente','🟡 Próximo'], default=[])
        
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
                           'Prom/mes','Cob.(m)','YTD 2026','Alerta','Pedido prop.','Fcst Jun','Fcst Jul']
        show_df['Prom/mes'] = show_df['Prom/mes'].round(1)
        show_df['Cob.(m)'] = show_df['Cob.(m)'].replace(99, '—')
        show_df['Pedido prop.'] = show_df['Pedido prop.'].apply(lambda x: int(x) if x > 0 else '—')
        show_df['Fcst Jun'] = show_df['Fcst Jun'].round(1)
        show_df['Fcst Jul'] = show_df['Fcst Jul'].round(1)
        
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
            sku = filtered.iloc[i]['SKU']
            orig_qty = filtered.iloc[i]['Pedido_propuesto']
            new_qty = row['Pedido prop.']
            if isinstance(new_qty, (int, float)) and new_qty != orig_qty:
                st.session_state['edited_pedido'][sku] = int(new_qty)
        
        st.caption(f"💡 Podés editar la columna 'Pedido prop.' directamente. Los cambios se reflejan en la pestaña Pedidos.")


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
                sku = prov_df.iloc[i]['SKU']
                new_cost = row['Precio unit. ARS']
                orig_cost = prov_df.iloc[i]['Costo_ARS']
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
                st.success(f"✓ {n_updated} precio(s) actualizado(s) en esta sesión. Se usarán en el PDF y en rentabilidad.")
            
            # Actions
            col_a, col_b, col_c = st.columns([1,1,3])
            with col_a:
                if st.button("📄 Descargar PDF", use_container_width=True, type="primary"):
                    edited_qtys = {prov_df.iloc[i]['SKU']: int(edited_prov.iloc[i]['Cantidad']) 
                                   for i in range(len(edited_prov))}
                    pdf_bytes = generate_pdf(prov_df, selected_prov, edited_qtys)
                    st.download_button(
                        label="⬇ Descargar PDF",
                        data=pdf_bytes,
                        file_name=f"Andina_Pedido_{selected_prov}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
            with col_b:
                if st.button("📋 Copiar para WhatsApp", use_container_width=True):
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
                q = alert_counts.get('🔴 Quiebre', 0)
                st.markdown(f'<div style="background:#f8d7da;border-radius:8px;padding:12px;text-align:center;"><div style="font-size:22px;font-weight:600;color:#721c24;">{q}</div><div style="font-size:11px;color:#721c24;">QUIEBRES</div></div>', unsafe_allow_html=True)
            with ac2:
                u = alert_counts.get('🟠 Urgente', 0)
                st.markdown(f'<div style="background:#fff3cd;border-radius:8px;padding:12px;text-align:center;"><div style="font-size:22px;font-weight:600;color:#856404;">{u}</div><div style="font-size:11px;color:#856404;">URGENTES</div></div>', unsafe_allow_html=True)
            with ac3:
                p = alert_counts.get('🟡 Próximo', 0)
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


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — RENTABILIDAD
# ═══════════════════════════════════════════════════════════════════════════════
with tabs[4]:
    if st.session_state['analysis_df'] is None:
        st.info("Completá los datos en Inicio primero.")
    else:
        adf = st.session_state['analysis_df']
        orders_df = st.session_state['orders_df']
        
        section_title("Rentabilidad por proveedora — últimos 3 meses")
        
        today = datetime.now()
        months_rent = [(today.year, m) for m in range(max(1, today.month-2), today.month+1)]
        
        monthly = {}
        for (yr, mo), grp in orders_df.groupby([orders_df['fecha'].dt.year, orders_df['fecha'].dt.month]):
            monthly[(int(yr), int(mo))] = grp.groupby('sku')['qty'].sum().to_dict()
        
        rows_r = []
        for sku, info in adf.set_index('SKU').iterrows():
            if info['Estado'] in ('BAJA','Borrador'): continue
            pn = info.get('Precio_normal'); pr = info.get('Precio_rebajado')
            has_pn = pd.notna(pn) and pn > 0
            has_pr = pd.notna(pr) and pr > 0
            en_sale = info['Estado'] == 'SALE'
            precio = float(pr) if (en_sale and has_pr) else (float(pn) if has_pn else None)
            
            costo = st.session_state['edited_costs'].get(sku, info.get('Costo_ARS'))
            has_cost = pd.notna(costo) and costo > 0 if costo is not None else False
            
            for (yr, mo) in months_rent:
                qty = monthly.get((yr, mo), {}).get(sku, 0)
                if qty <= 0: continue
                ing = qty * precio if precio else None
                cst = qty * float(costo) if (has_cost and costo) else None
                mrg = ing - cst if (ing is not None and cst is not None) else None
                mrg_pct = mrg/ing if (mrg is not None and ing and ing > 0) else None
                rows_r.append({
                    'SKU': sku, 'Nombre': info['Nombre'], 'Proveedor': info['Proveedor'],
                    'Mes': f"{yr}-{mo:02d}", 'Unidades': int(qty),
                    'Precio': precio, 'Costo': float(costo) if has_cost else None,
                    'Ingresos': ing, 'Costo_total': cst, 'Margen': mrg, 'Margen_pct': mrg_pct,
                    'tiene_costo': has_cost,
                })
        
        if not rows_r:
            st.warning("No hay datos de rentabilidad para calcular. Verificá que los costos estén cargados.")
        else:
            df_r = pd.DataFrame(rows_r)
            
            # By provider summary
            prov_r = []
            for prov, grp in df_r.groupby('Proveedor'):
                if not prov: continue
                gw = grp[grp['tiene_costo']]
                ut = grp['Unidades'].sum(); uw = gw['Unidades'].sum()
                iw = gw['Ingresos'].dropna().sum(); cw = gw['Costo_total'].dropna().sum()
                mw = gw['Margen'].dropna().sum(); mp = mw/iw if iw > 0 else None
                iwo = grp[~grp['tiene_costo']]['Ingresos'].dropna().sum()
                cob = uw/ut if ut > 0 else 0
                nota = '⚠ Sin costos' if uw == 0 else (f'~{cob:.0%} cubierto' if cob < 0.9 else '✓ Completo')
                prov_r.append({
                    'Proveedora': prov, 'Uds total': int(ut), 'Uds c/costo': int(uw),
                    'Cobertura': f"{cob:.0%}", 'Ingresos (c/costo)': int(iw) if iw > 0 else None,
                    'Costo total': int(cw) if cw > 0 else None,
                    'Margen $': int(mw) if mw else None,
                    'Margen %': f"{mp:.1%}" if mp is not None else '—',
                    'Ing. sin costo': int(iwo) if iwo > 0 else None,
                    'Nota': nota,
                })
            
            prov_r_df = pd.DataFrame(prov_r).sort_values('Margen $', ascending=False, na_position='last')
            st.dataframe(prov_r_df, use_container_width=True, hide_index=True)
            
            # Coverage note
            total_u = df_r['Unidades'].sum()
            u_con = df_r[df_r['tiene_costo']]['Unidades'].sum()
            st.caption(f"Cobertura: {u_con}/{total_u} unidades ({u_con/total_u:.0%}) tienen costo cargado. Cargá el archivo de costos completo para mejorar la cobertura.")
