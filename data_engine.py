"""
Core data engine — all business logic for Andina inventory & orders system.
Processes WooCommerce exports and costs file to generate analysis.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st

KNOWN_PROVS = {
    'DEBY R','DECIMO','DORIS V','DUA','FRANCO','KAIRA','LATE','LUZ',
    'MARCIA','MARINA F','MUESTRA','NORTE','PAULA P','ROCIO A','SOL D','SOL S','VITULA'
}

# ── LOADERS ───────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_orders(file) -> pd.DataFrame:
    """Load WooCommerce orders export. Handles both full-history and monthly files."""
    try:
        df = pd.read_excel(file)
    except Exception:
        df = pd.read_csv(file)
    
    # Normalize date column
    date_col = next((c for c in df.columns if 'fecha' in c.lower() and 'pedido' in c.lower()), None)
    if date_col:
        df['fecha'] = pd.to_datetime(df[date_col], errors='coerce')
    
    sku_col = next((c for c in df.columns if c.strip().upper() == 'SKU'), None)
    if sku_col:
        df['sku'] = df[sku_col].astype(str).str.strip()
    
    # Remove gift cards
    df = df[~df['sku'].str.startswith('GC', na=False)]
    df = df[df['sku'].notna() & (df['sku'] != 'nan') & (df['sku'] != '')]
    
    # Qty: if file has Cantidad col use it; otherwise 1 row = 1 unit
    qty_col = next((c for c in df.columns if 'cantidad' in c.lower()), None)
    if qty_col:
        df['qty'] = pd.to_numeric(df[qty_col], errors='coerce').fillna(1)
    else:
        df['qty'] = 1
    
    return df[['fecha','sku','qty']].dropna(subset=['fecha','sku'])


def load_inventory(file) -> pd.DataFrame:
    """Load WooCommerce product export CSV."""
    try:
        df = pd.read_csv(file, low_memory=False)
    except Exception:
        df = pd.read_excel(file)
    
    df.columns = df.columns.str.strip()
    
    # Normalize columns
    col_map = {}
    for c in df.columns:
        cl = c.lower()
        if cl == 'sku': col_map[c] = 'SKU'
        elif 'nombre' in cl or 'name' in cl: col_map[c] = 'Nombre'
        elif 'inventario' in cl or 'stock' in cl: col_map[c] = 'Inventario'
        elif 'publicado' in cl: col_map[c] = 'Publicado'
        elif 'precio normal' in cl or 'regular price' in cl: col_map[c] = 'Precio_normal'
        elif 'rebajado' in cl or 'sale price' in cl: col_map[c] = 'Precio_rebajado'
        elif 'imagen' in cl or 'image' in cl: col_map[c] = 'Imagen'
        elif 'categoría' in cl or 'category' in cl: col_map[c] = 'Categoria'
    df = df.rename(columns=col_map)
    
    def safe_numeric(series, fill=0):
        """Convert to numeric safely, handling duplicate columns and mixed types."""
        # If duplicate columns caused a DataFrame, take the first column
        if isinstance(series, pd.DataFrame):
            series = series.iloc[:, 0]
        series = series.astype(str)
        # First pass: direct numeric conversion
        result = pd.to_numeric(series, errors='coerce')
        # Second pass: regex extraction for values that failed
        if result.isna().any():
            extracted = series.str.extract(r'([-\d.]+)', expand=False)
            result = result.fillna(pd.to_numeric(extracted, errors='coerce'))
        return result.fillna(fill)
    
    if 'Inventario' in df.columns:
        df['Inventario'] = safe_numeric(df['Inventario'], fill=0)
    else:
        df['Inventario'] = 0
    if 'Publicado' in df.columns:
        df['Publicado'] = safe_numeric(df['Publicado'], fill=0)
    else:
        df['Publicado'] = 0
    if 'Precio_normal' in df.columns:
        df['Precio_normal'] = safe_numeric(df['Precio_normal'], fill=0).replace(0, float('nan'))
    else:
        df['Precio_normal'] = float('nan')
    if 'Precio_rebajado' in df.columns:
        df['Precio_rebajado'] = safe_numeric(df['Precio_rebajado'], fill=0).replace(0, float('nan'))
    else:
        df['Precio_rebajado'] = float('nan')
    
    # Estado
    def get_estado(r):
        has_rebajado = pd.notna(r.get('Precio_rebajado')) and r.get('Precio_rebajado', 0) > 0
        if has_rebajado: return 'SALE'
        if r.get('Publicado') == 1: return 'Activo'
        return 'Borrador'
    df['Estado'] = df.apply(get_estado, axis=1)
    
    # Image URL — first URL from comma-separated list
    if 'Imagen' in df.columns:
        df['Imagen_url'] = df['Imagen'].astype(str).apply(
            lambda x: x.split(',')[0].strip() if x and x != 'nan' else '')
    else:
        df['Imagen_url'] = ''
    
    # Infer type from category or SKU
    def infer_tipo(row):
        cat = str(row.get('Categoria', '')).lower()
        sku = str(row.get('SKU', '')).upper()
        if 'pulsera' in cat or 'brazalete' in cat or sku[:2] in ('PU','BR'): return 'Pulsera'
        if 'anillo' in cat or sku[:2] == 'AN': return 'Anillo'
        if 'aro' in cat or sku[:2] == 'AR': return 'Aro'
        if 'collar largo' in cat or sku[:2] == 'LC': return 'Collar Largo'
        if 'gargantilla' in cat or 'collar' in cat or sku[:2] == 'CO': return 'Gargantilla'
        if 'conjunto' in cat or sku[:2] in ('CS','CJ'): return 'Conjunto'
        if 'accesorio' in cat or sku[:2] == 'AC': return 'Accesorio'
        return 'Accesorio'
    df['Tipo'] = df.apply(infer_tipo, axis=1)
    
    df['SKU'] = df['SKU'].astype(str).str.strip()
    return df


@st.cache_data(show_spinner=False)
def load_costs(file) -> pd.DataFrame:
    """Load costs file — Costo_proveedoras format."""
    try:
        raw = pd.read_excel(file, sheet_name='COSTOS', header=1)
    except Exception:
        try:
            raw = pd.read_excel(file, header=1)
        except Exception:
            raw = pd.read_csv(file)
    
    raw.columns = ['Proveedor','SKU','Nombre_Prov','SKU_Prov','Costo_ARS',
                   'Fecha_Lista','Notas','Estado_WC','Costo_Anterior','Cambio','Foto'][:len(raw.columns)]
    
    raw = raw[
        raw['SKU'].notna() &
        ~raw['Proveedor'].astype(str).str.contains('──', na=False) &
        (raw['SKU'].astype(str).str.strip() != 'SKU Andina') &
        (raw['SKU'].astype(str).str.strip() != 'SKU')
    ].copy()
    
    raw['Costo_ARS'] = pd.to_numeric(raw['Costo_ARS'], errors='coerce')
    raw['SKU'] = raw['SKU'].astype(str).str.strip()
    raw['Proveedor'] = raw['Proveedor'].astype(str).str.strip()
    return raw


# ── CORE ENGINE ───────────────────────────────────────────────────────────────

def build_monthly_sales(orders_df: pd.DataFrame) -> dict:
    """Returns {(year, month): {sku: qty}} from orders dataframe."""
    result = {}
    for (y, m), grp in orders_df.groupby([orders_df['fecha'].dt.year, orders_df['fecha'].dt.month]):
        result[(int(y), int(m))] = grp.groupby('sku')['qty'].sum().to_dict()
    return result


def get_month_sales(monthly: dict, year: int, month: int) -> dict:
    return monthly.get((year, month), {})


def compute_abcd(sku_ytd: dict, exclude_estados: set = None) -> dict:
    """
    ABCD ranking based on YTD cumulative sales share.
    A = top 50%, B = 50-80%, C = 80-90%, D = 90-100%
    New products (sem_vida <= 12 weeks) = A
    Returns {sku: rank}
    """
    items = [(sku, qty) for sku, qty in sku_ytd.items() if qty > 0]
    items.sort(key=lambda x: -x[1])
    total = sum(q for _, q in items)
    
    result = {sku: 'D' for sku in sku_ytd}  # default D
    
    if total == 0:
        return result
    
    cum = 0
    for sku, qty in items:
        cum += qty
        pct = cum / total
        if pct <= 0.50:
            result[sku] = 'A'
        elif pct <= 0.80:
            result[sku] = 'B'
        elif pct <= 0.90:
            result[sku] = 'C'
        else:
            result[sku] = 'D'
    return result


def compute_primera_venta(orders_df: pd.DataFrame) -> dict:
    """Returns {sku: first_sale_date}"""
    return orders_df.groupby('sku')['fecha'].min().to_dict()


def compute_sem_vida(primera_venta: dict, ref_date: datetime = None) -> dict:
    """Returns {sku: weeks_since_first_sale}"""
    ref = ref_date or datetime.now()
    result = {}
    for sku, fv in primera_venta.items():
        if pd.notna(fv):
            delta = ref - pd.Timestamp(fv)
            result[sku] = max(0, delta.days / 7)
    return result


def compute_forecast(
    jun_total: int,
    jul_total: int,
    prov_mix: dict,       # {prov: share 0-1}
    prov_sku_ytd: dict,   # {prov: {sku: ytd_qty}}
) -> dict:
    """
    Returns {sku: {'jun': float, 'jul': float}}
    Uses: sku_share_within_prov * prov_total_units
    """
    result = {}
    for prov, sku_ytd in prov_sku_ytd.items():
        prov_total_ytd = sum(sku_ytd.values()) or 1
        prov_mix_val = prov_mix.get(prov, 0)
        prov_jun = jun_total * prov_mix_val
        prov_jul = jul_total * prov_mix_val
        for sku, ytd in sku_ytd.items():
            share = ytd / prov_total_ytd
            result[sku] = {
                'jun': round(share * prov_jun, 1),
                'jul': round(share * prov_jul, 1),
            }
    return result


def compute_pedido_propuesto(
    sku: str,
    inv: float,
    prom_mensual: float,
    lead_time_weeks: float,
    cobertura_objetivo_weeks: float = 6.0,
) -> int:
    """target = prom * (lead_time + safety) / 4.3 — inv"""
    if prom_mensual <= 0:
        return 0
    target = prom_mensual * (lead_time_weeks + cobertura_objetivo_weeks) / 4.3
    proposed = max(0, round(target - inv))
    return int(proposed)


def build_analysis_df(
    inv_df: pd.DataFrame,
    orders_all: pd.DataFrame,
    costs_df: pd.DataFrame,
    prov_params: dict,
    jun_total: int,
    jul_total: int,
    prov_mix_override: dict,
    ref_date: datetime = None,
) -> pd.DataFrame:
    """
    Master function — builds the full SKU analysis dataframe.
    """
    ref = ref_date or datetime.now()
    today_year = ref.year
    today_month = ref.month
    
    # Build monthly sales
    monthly = build_monthly_sales(orders_all)
    
    # YTD: Jan to current month of current year
    ytd_months = [(today_year, m) for m in range(1, today_month + 1)]
    
    # Per SKU YTD
    sku_ytd = {}
    for ym in ytd_months:
        for sku, qty in monthly.get(ym, {}).items():
            sku_ytd[sku] = sku_ytd.get(sku, 0) + qty
    
    # Monthly sales per SKU for last 12 months (for sparklines & prom)
    monthly_per_sku = {}  # sku -> list of (year_month_label, qty)
    for offset in range(11, -1, -1):
        yr = today_year if today_month - offset > 0 else today_year - 1
        mo = (today_month - offset - 1) % 12 + 1
        label = f"{yr}-{mo:02d}"
        month_data = monthly.get((yr, mo), {})
        for sku, qty in month_data.items():
            if sku not in monthly_per_sku:
                monthly_per_sku[sku] = {}
            monthly_per_sku[sku][label] = qty
    
    # Primera venta & sem_vida
    primera_venta = compute_primera_venta(orders_all)
    sem_vida = compute_sem_vida(primera_venta, ref)
    
    # Costs lookup
    cost_map = dict(zip(costs_df['SKU'], costs_df['Costo_ARS']))
    nombre_prov_map = dict(zip(costs_df['SKU'], costs_df.get('Nombre_Prov', pd.Series(dtype=str))))
    sku_prov_map = dict(zip(costs_df['SKU'], costs_df.get('SKU_Prov', pd.Series(dtype=str))))
    proveedor_map = dict(zip(costs_df['SKU'], costs_df['Proveedor']))
    
    # Build rows — start from inventory (source of truth for active products)
    rows = []
    woo_skus = set(inv_df['SKU'].astype(str))
    
    # All SKUs = union of inventory + historical sales
    all_skus = woo_skus | set(orders_all['sku'].unique())
    
    for sku in all_skus:
        if sku.startswith('GC') or not sku or sku == 'nan':
            continue
        
        inv_row = inv_df[inv_df['SKU'] == sku]
        
        # Estado
        if not inv_row.empty:
            estado = inv_row.iloc[0]['Estado']
            inv_qty = int(inv_row.iloc[0].get('Inventario', 0))
            nombre = str(inv_row.iloc[0].get('Nombre', ''))
            tipo = str(inv_row.iloc[0].get('Tipo', ''))
            precio_normal = inv_row.iloc[0].get('Precio_normal', None)
            precio_rebajado = inv_row.iloc[0].get('Precio_rebajado', None)
            imagen_url = str(inv_row.iloc[0].get('Imagen_url', ''))
        else:
            estado = 'BAJA'  # not in WooCommerce
            inv_qty = 0
            nombre = ''
            tipo = ''
            precio_normal = None
            precio_rebajado = None
            imagen_url = ''
        
        # Proveedor
        prov = proveedor_map.get(sku, '')
        nombre_prov = str(nombre_prov_map.get(sku, '') or '')
        sku_prov = str(sku_prov_map.get(sku, '') or '')
        
        # Sem vida & nuevo
        sv = sem_vida.get(sku, 0)
        primera = primera_venta.get(sku, None)
        is_nuevo = sv <= 12  # less than 3 months
        
        # YTD & monthly
        ytd = sku_ytd.get(sku, 0)
        months_with_sales = sum(1 for ym in ytd_months if monthly.get(ym, {}).get(sku, 0) > 0)
        prom = ytd / months_with_sales if months_with_sales > 0 else 0
        
        # 2025 same period YTD for comparison
        ytd_2025 = sum(monthly.get((2025, m), {}).get(sku, 0) for m in range(1, today_month + 1))
        
        rows.append({
            'SKU': sku,
            'Nombre': nombre,
            'Tipo': tipo,
            'Proveedor': prov,
            'Nombre_Prov': nombre_prov,
            'SKU_Prov': sku_prov,
            'Estado': estado,
            'Inventario': inv_qty,
            'Precio_normal': precio_normal,
            'Precio_rebajado': precio_rebajado,
            'Imagen_url': imagen_url,
            'YTD_2026': ytd,
            'YTD_2025': ytd_2025,
            'Meses_con_ventas': months_with_sales,
            'Prom_mensual': round(prom, 2),
            'Sem_vida': round(sv, 1),
            'Primera_venta': primera,
            'Es_nuevo': is_nuevo,
            'Costo_ARS': cost_map.get(sku, None),
            'monthly_data': monthly_per_sku.get(sku, {}),
        })
    
    df = pd.DataFrame(rows)
    
    # ABCD — only on Activo/Nuevo, exclude Borrador/BAJA
    active_mask = df['Estado'].isin(['Activo', 'SALE'])
    sku_ytd_active = dict(zip(df[active_mask]['SKU'], df[active_mask]['YTD_2026']))
    abcd = compute_abcd(sku_ytd_active)
    
    df['Prior'] = df['SKU'].map(abcd).fillna('D')
    # Nuevos get A unless they're Borrador/BAJA
    df.loc[df['Es_nuevo'] & active_mask, 'Prior'] = 'A'
    # Borrador/BAJA always D
    df.loc[df['Estado'].isin(['Borrador','BAJA']), 'Prior'] = 'D'
    
    # Cobertura in months
    df['Cobertura_meses'] = df.apply(
        lambda r: round(r['Inventario'] / r['Prom_mensual'], 1) if r['Prom_mensual'] > 0 else 99, axis=1)
    
    # Pedido propuesto
    def get_pedido(row):
        if row['Estado'] in ('BAJA', 'Borrador', 'SALE'):
            return 0
        if row['Prior'] not in ('A', 'B') and not row['Es_nuevo']:
            return 0
        params = prov_params.get(row['Proveedor'], {'lt': 2, 'cob': 6})
        return compute_pedido_propuesto(
            row['SKU'], row['Inventario'], row['Prom_mensual'],
            params['lt'], params['cob'])
    
    df['Pedido_propuesto'] = df.apply(get_pedido, axis=1)
    
    # Forecast Jun/Jul
    prov_sku_ytd = {}
    for _, row in df[df['Proveedor'] != ''].iterrows():
        p = row['Proveedor']
        if p not in prov_sku_ytd:
            prov_sku_ytd[p] = {}
        prov_sku_ytd[p][row['SKU']] = row['YTD_2026']
    
    # Build prov_mix from prov_mix_override or from YTD data
    total_ytd_all = df[df['Estado'].isin(['Activo','SALE'])]['YTD_2026'].sum()
    prov_mix = {}
    for prov in KNOWN_PROVS:
        if prov in prov_mix_override:
            prov_mix[prov] = prov_mix_override[prov]
        else:
            prov_ytd_val = df[df['Proveedor'] == prov]['YTD_2026'].sum()
            prov_mix[prov] = prov_ytd_val / total_ytd_all if total_ytd_all > 0 else 0
    
    fcst = compute_forecast(jun_total, jul_total, prov_mix, prov_sku_ytd)
    df['Fcst_Jun'] = df['SKU'].map(lambda s: fcst.get(s, {}).get('jun', 0))
    df['Fcst_Jul'] = df['SKU'].map(lambda s: fcst.get(s, {}).get('jul', 0))
    
    # Alert type
    def get_alerta(row):
        if row['Estado'] in ('BAJA','Borrador'): return ''
        inv = row['Inventario']; prom = row['Prom_mensual']; cob = row['Cobertura_meses']
        prior = row['Prior']; in_sale = row['Estado'] == 'SALE'
        if inv == 0 and prom > 0 and not in_sale and prior in ('A','B','C'):
            return '🔴 Quiebre'
        if inv > 0 and cob < 1 and prom > 0 and not in_sale and prior in ('A','B'):
            return '🟠 Urgente'
        if inv > 0 and 1 <= cob < 2 and prior in ('A','B') and not in_sale:
            return '🟡 Próximo'
        return ''
    
    df['Alerta'] = df.apply(get_alerta, axis=1)
    
    return df


def get_historical_monthly(orders_df: pd.DataFrame) -> pd.DataFrame:
    """Returns monthly totals for 2022-2026 for the chart."""
    orders_df['year'] = orders_df['fecha'].dt.year
    orders_df['month'] = orders_df['fecha'].dt.month
    monthly = orders_df.groupby(['year','month'])['qty'].sum().reset_index()
    monthly.columns = ['year','month','units']
    return monthly


def yoy_for_month(historical: pd.DataFrame, year: int, month: int) -> dict:
    """Returns {year_val, prev_year_val, yoy_pct} for a given month."""
    curr = historical[(historical['year']==year) & (historical['month']==month)]['units'].sum()
    prev = historical[(historical['year']==year-1) & (historical['month']==month)]['units'].sum()
    yoy = (curr/prev - 1) if prev > 0 else None
    return {'curr': int(curr), 'prev': int(prev), 'yoy': yoy}
