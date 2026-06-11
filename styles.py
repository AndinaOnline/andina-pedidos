# Andina — estilos. Paleta estricta del Manual de Marca + estética web (blanco cálido).
COLORS = {
    "rosa":        "#F9DDDE",   # rosa primario (acento)
    "terra":       "#D99352",   # ocre/dorado secundario (acento principal)
    "gris":        "#EBE8E6",   # accesorio fondos / bordes
    "texto":       "#606060",   # texto cuerpo
    "oscuro":      "#3A3A3A",   # títulos (negro suave de la web)
    "blanco":      "#FFFFFF",
    "crema":       "#FAF7F5",   # fondo cálido dominante (como la web)
    "rosa_borde":  "#EFD3D4",
    "terra_claro": "#FBEFE2",
    # funcionales
    "verde_ok":    "#5A9A8A",
    "rojo_alerta": "#C0392B",
    "naranja":     "#D99352",
    "verde_agua":  "#F2EFEA",
    "arena":       "#E0D9D1",
    "negro":       "#3A3A3A",
    "gris_texto":  "#606060",
}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Raleway:wght@300;400;500;600;700&display=swap');

.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"],
.main, [data-testid="stMain"], .block-container {{ background: #FFFFFF !important; }}
html, body, [class*="css"] {{
    font-family: 'Raleway', sans-serif;
    color: {COLORS['texto']};
}}
.block-container {{ padding-top: 1rem; padding-bottom: 2rem; max-width: 1120px; }}

/* ── HEADER ── */
.andina-header {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 4px 16px; margin-bottom: 18px;
    border-bottom: 1px solid {COLORS['rosa_borde']};
}}
.andina-logo-img {{ height: 56px; width: auto; display: block; }}
.andina-header-right {{
    font-family: 'Raleway', sans-serif; font-size: 11px;
    color: {COLORS['texto']}; text-align: right; letter-spacing: 0.5px;
}}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; background: transparent; margin-bottom: 10px; }}
.stTabs [data-baseweb="tab"] {{
    font-family: 'Raleway', sans-serif; font-size: 11px; font-weight: 500;
    text-transform: uppercase; letter-spacing: 1.8px; color: {COLORS['texto']};
    background: {COLORS['blanco']}; border: 1px solid {COLORS['gris']};
    border-radius: 4px; padding: 9px 20px;
}}
.stTabs [aria-selected="true"] {{
    background: {COLORS['blanco']} !important; color: {COLORS['terra']} !important;
    border-color: {COLORS['terra']} !important; font-weight: 600 !important;
}}

/* ── SECTION TITLES (Raleway mayúscula — manual de marca) ── */
.section-title {{
    font-family: 'Raleway', sans-serif; font-weight: 600;
    font-size: 12px; text-transform: uppercase; letter-spacing: 2.5px;
    color: {COLORS['oscuro']};
    margin: 22px 0 12px; padding-bottom: 7px;
    border-bottom: 1px solid {COLORS['gris']};
}}

/* ── CARDS ── */
.andina-card {{
    background: {COLORS['blanco']}; border: 1px solid {COLORS['gris']};
    border-radius: 8px; padding: 18px 20px; margin-bottom: 14px;
}}

/* ── UPLOAD ── */
.upload-ok {{
    background: #F2EFEA; border: 1px solid {COLORS['arena']}; border-left: 3px solid {COLORS['terra']};
    border-radius: 6px; padding: 12px 14px; text-align: center; font-size: 12px;
    color: {COLORS['oscuro']}; font-family: 'Raleway', sans-serif;
}}
.upload-pending {{
    background: {COLORS['terra_claro']}; border: 1px dashed {COLORS['terra']};
    border-radius: 6px; padding: 12px 14px; text-align: center; font-size: 12px;
    color: {COLORS['texto']}; font-family: 'Raleway', sans-serif;
}}

/* ── BADGES ── */
.badge {{ display: inline-block; padding: 2px 9px; border-radius: 4px; font-size: 11px; font-weight: 600; font-family: 'Raleway', sans-serif; }}
.badge-a  {{ background: {COLORS['terra_claro']}; color: #7d4e00; }}
.badge-b  {{ background: {COLORS['rosa']}; color: #8a3a3a; }}
.badge-c  {{ background: {COLORS['gris']}; color: {COLORS['texto']}; }}
.badge-d  {{ background: {COLORS['gris']}; color: {COLORS['texto']}; }}
.badge-activo   {{ background: {COLORS['terra_claro']}; color: #7d4e00; }}
.badge-nuevo    {{ background: {COLORS['rosa']}; color: #8a3a3a; }}
.badge-sale     {{ background: {COLORS['rosa']}; color: #8a3a3a; }}
.badge-borrador {{ background: {COLORS['gris']}; color: {COLORS['texto']}; }}
.badge-baja     {{ background: {COLORS['gris']}; color: {COLORS['texto']}; }}

/* ── PEDIDO TOTAL ── */
.pedido-total {{
    background: {COLORS['oscuro']}; color: {COLORS['terra']}; border-radius: 8px;
    padding: 14px 20px; display: flex; justify-content: space-between; align-items: center;
    margin-top: 14px; font-family: 'Raleway', sans-serif;
}}

/* ── OVERRIDES ── */
div[data-testid="stButton"] > button {{ font-family:'Raleway',sans-serif; font-size:12px; letter-spacing:0.5px; border-radius:6px; }}
div[data-testid="stButton"] > button[kind="primary"] {{ background:{COLORS['terra']}; color:white; border:none; }}
div[data-testid="stFileUploader"] label, div[data-testid="stNumberInput"] label, div[data-testid="stSelectbox"] label {{
    font-family:'Raleway',sans-serif; font-size:11px; text-transform:uppercase; letter-spacing:1px; color:{COLORS['texto']};
}}
div[data-testid="stMetric"] {{ background:{COLORS['blanco']}; border:1px solid {COLORS['gris']}; border-radius:8px; padding:12px 16px; }}
div[data-testid="stMetric"] label {{ font-family:'Raleway',sans-serif; font-size:10px; text-transform:uppercase; letter-spacing:1.5px; color:{COLORS['texto']}; }}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {{ font-family:'Raleway',sans-serif; font-size:23px; font-weight:600; color:{COLORS['oscuro']}; }}
div[data-testid="stDataFrame"] {{ border:1px solid {COLORS['gris']}; border-radius:8px; }}
.stMultiSelect [data-baseweb="tag"] {{ background:{COLORS['rosa']}; color:{COLORS['oscuro']}; }}
</style>
"""

import os, base64

def _logo_b64():
    path = os.path.join(os.path.dirname(__file__), 'assets', 'andina_logo.png')
    try:
        with open(path, 'rb') as fh:
            return base64.b64encode(fh.read()).decode()
    except Exception:
        return ''

def render_header(subtitle="Sistema de Pedidos"):
    import streamlit as st
    b64 = _logo_b64()
    logo = (f'<img class="andina-logo-img" src="data:image/png;base64,{b64}" alt="Andina">'
            if b64 else '<div style="font-family:Raleway,sans-serif;font-weight:600;letter-spacing:2px;font-size:22px;color:#3A3A3A;">Andina</div>')
    st.markdown(f"""
    <div class="andina-header">
        {logo}
        <div class="andina-header-right">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def section_title(text):
    import streamlit as st
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)
