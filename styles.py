# Andina brand colors — strictly from Manual de Marca
COLORS = {
    "rosa":        "#F9DDDE",   # primario rosa
    "terra":       "#D99352",   # secundario ocre/dorado — accent
    "gris":        "#EBE8E6",   # accesorio para fondos
    "texto":       "#606060",   # color para textos
    "oscuro":      "#000000",   # negro 100% — títulos
    "blanco":      "#FFFFFF",   # fondo principal
    "rosa_borde":  "#EFD3D4",   # borde suave sobre rosa
    "terra_claro": "#FBEFE2",   # tinte ocre claro para fondos
    # Funcionales (semáforo) — fuera de paleta de marca, solo para estados
    "verde_ok":    "#27AE60",
    "rojo_alerta": "#C0392B",
    "naranja":     "#E67E22",
    "azul":        "#2980B9",
    "verde_agua":  "#E8F5E9",
    "arena":       "#E0D9D1",
    "negro":       "#000000",
    "gris_texto":  "#606060",
}

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Raleway:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'Raleway', sans-serif;
    color: {COLORS['texto']};
    background-color: {COLORS['blanco']};
}}
.block-container {{
    padding-top: 0rem;
    padding-bottom: 2rem;
    max-width: 1100px;
}}

/* ── HEADER ────────────────────────────────────────────────────────── */
.andina-header {{
    background: {COLORS['blanco']};
    border-bottom: 1px solid {COLORS['gris']};
    padding: 18px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
}}
.andina-logo-img {{
    height: 46px;
    width: auto;
    display: block;
}}
.andina-tagline {{
    font-family: 'Raleway', sans-serif;
    font-size: 9px;
    color: {COLORS['texto']};
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 2px;
}}
.andina-header-right {{
    font-family: 'Raleway', sans-serif;
    font-size: 11px;
    color: {COLORS['texto']};
    text-align: right;
    letter-spacing: 0.5px;
}}

/* ── NAVIGATION TABS ────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
    gap: 6px;
    background: transparent;
    padding: 0;
    margin-bottom: 8px;
}}
.stTabs [data-baseweb="tab"] {{
    font-family: 'Raleway', sans-serif;
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: {COLORS['texto']};
    background: {COLORS['blanco']};
    border: 1px solid {COLORS['gris']};
    border-radius: 6px;
    padding: 8px 18px;
    transition: all 0.2s;
}}
.stTabs [aria-selected="true"] {{
    background: {COLORS['terra_claro']} !important;
    color: {COLORS['terra']} !important;
    border-color: {COLORS['terra']} !important;
    font-weight: 600 !important;
}}

/* ── SECTION TITLES ─────────────────────────────────────────────────── */
.section-title {{
    font-family: 'Raleway', sans-serif;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 2.5px;
    color: {COLORS['texto']};
    margin-bottom: 10px;
    margin-top: 20px;
    padding-bottom: 6px;
    border-bottom: 1px solid {COLORS['gris']};
}}

/* ── CARDS ──────────────────────────────────────────────────────────── */
.andina-card {{
    background: {COLORS['blanco']};
    border: 1px solid {COLORS['gris']};
    border-radius: 8px;
    padding: 18px 20px;
    margin-bottom: 14px;
}}

/* ── UPLOAD ZONES ───────────────────────────────────────────────────── */
.upload-ok {{
    background: #e8f5e9;
    border: 1px solid #a5d6a7;
    border-radius: 8px;
    padding: 14px 16px;
    text-align: center;
    font-size: 13px;
    color: #2e7d32;
    font-family: 'Raleway', sans-serif;
}}
.upload-pending {{
    background: {COLORS['terra_claro']};
    border: 1px dashed {COLORS['terra']};
    border-radius: 8px;
    padding: 14px 16px;
    text-align: center;
    font-size: 13px;
    color: {COLORS['texto']};
    font-family: 'Raleway', sans-serif;
}}

/* ── BADGES / RANKINGS ──────────────────────────────────────────────── */
.badge {{
    display: inline-block;
    padding: 2px 9px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    font-family: 'Raleway', sans-serif;
}}
.badge-a  {{ background: #e8f5e9; color: #2e7d32; }}
.badge-b  {{ background: {COLORS['terra_claro']}; color: #7d4e00; }}
.badge-c  {{ background: {COLORS['terra_claro']}; color: {COLORS['terra']}; }}
.badge-d  {{ background: {COLORS['gris']}; color: {COLORS['texto']}; }}
.badge-activo   {{ background: #e8f5e9; color: #2e7d32; }}
.badge-nuevo    {{ background: {COLORS['terra_claro']}; color: #7d4e00; }}
.badge-sale     {{ background: {COLORS['rosa']}; color: {COLORS['oscuro']}; }}
.badge-borrador {{ background: {COLORS['gris']}; color: {COLORS['texto']}; }}
.badge-baja     {{ background: #fce4ec; color: #880e4f; }}

/* ── PEDIDO TOTAL BAR ───────────────────────────────────────────────── */
.pedido-total {{
    background: {COLORS['oscuro']};
    color: {COLORS['terra']};
    border-radius: 8px;
    padding: 14px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 14px;
    font-family: 'Raleway', sans-serif;
}}

/* ── STREAMLIT OVERRIDES ────────────────────────────────────────────── */
div[data-testid="stButton"] > button {{
    font-family: 'Raleway', sans-serif;
    font-size: 12px;
    letter-spacing: 0.5px;
    border-radius: 6px;
}}
div[data-testid="stButton"] > button[kind="primary"] {{
    background: {COLORS['terra']};
    color: white;
    border: none;
}}
div[data-testid="stSelectbox"] label,
div[data-testid="stNumberInput"] label,
div[data-testid="stTextInput"] label,
div[data-testid="stFileUploader"] label {{
    font-family: 'Raleway', sans-serif;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: {COLORS['texto']};
}}
div[data-testid="stMetric"] {{
    background: {COLORS['blanco']};
    border: 1px solid {COLORS['gris']};
    border-radius: 8px;
    padding: 12px 16px;
}}
div[data-testid="stMetric"] label {{
    font-family: 'Raleway', sans-serif;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: {COLORS['texto']};
}}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
    font-family: 'Raleway', sans-serif;
    font-size: 22px;
    font-weight: 600;
    color: {COLORS['oscuro']};
}}
div[data-testid="stDataFrame"] {{
    border: 1px solid {COLORS['gris']};
    border-radius: 8px;
}}
div[data-testid="stAlert"] {{
    border-radius: 8px;
    font-family: 'Raleway', sans-serif;
}}
.stMultiSelect [data-baseweb="tag"] {{
    background: {COLORS['rosa']};
    color: {COLORS['oscuro']};
}}
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
    from datetime import datetime
    fecha = datetime.now().strftime('%d/%m/%Y')
    b64 = _logo_b64()
    logo_html = (f'<img class="andina-logo-img" src="data:image/png;base64,{b64}" alt="Andina">'
                 if b64 else '<div style="font-size:24px;color:#D99352;">Andina</div>')
    st.markdown(f"""
    <div class="andina-header">
        <div style="display:flex; align-items:center; gap:16px;">
            {logo_html}
        </div>
        <div class="andina-header-right">
            <div style="font-weight:500; color:{COLORS['oscuro']};">{subtitle}</div>
            <div style="font-size:10px; margin-top:2px;">{fecha}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def section_title(text):
    import streamlit as st
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)
