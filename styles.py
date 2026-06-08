# Andina brand colors from manual de marca
COLORS = {
    "rosa_palido": "#FBDBDB",      # primary background
    "arena":       "#DFCEC0",      # secondary
    "verde_agua":  "#EAEDE8",      # accent background
    "gris_texto":  "#5D6364",      # body text
    "negro":       "#000000",      # headings
    "blanco":      "#FFFFFF",
    # Functional
    "alerta_roja": "#C0392B",
    "alerta_naranja": "#E67E22",
    "alerta_amarilla": "#F39C12",
    "verde_ok":    "#27AE60",
    "azul_info":   "#2980B9",
}

FONT = "Raleway"   # Google Font loaded via CSS

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Raleway:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {{
    font-family: 'Raleway', sans-serif;
    color: {COLORS['gris_texto']};
    background-color: {COLORS['rosa_palido']};
}}

/* Main container */
.block-container {{
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1100px;
}}

/* Header bar */
.andina-header {{
    background: {COLORS['arena']};
    color: {COLORS['negro']};
    padding: 14px 24px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
    border: 0.5px solid #c9b8a8;
}}
.andina-logo {{
    font-size: 26px;
    font-style: italic;
    color: {COLORS['negro']};
    letter-spacing: 1px;
}}
.andina-subtitle {{
    font-size: 11px;
    color: {COLORS['gris_texto']};
    letter-spacing: 2px;
    text-transform: uppercase;
}}

/* Cards */
.andina-card {{
    background: {COLORS['blanco']};
    border: 0.5px solid {COLORS['arena']};
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 14px;
}}
.andina-card-rosa {{
    background: {COLORS['rosa_palido']};
    border: 0.5px solid {COLORS['arena']};
    border-radius: 10px;
    padding: 16px 18px;
    margin-bottom: 12px;
}}

/* Metric cards */
.metric-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 10px;
    margin-bottom: 16px;
}}
.metric-box {{
    background: {COLORS['blanco']};
    border: 0.5px solid {COLORS['arena']};
    border-radius: 8px;
    padding: 12px 14px;
    text-align: center;
}}
.metric-label {{
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: {COLORS['gris_texto']};
    margin-bottom: 4px;
}}
.metric-value {{
    font-size: 22px;
    font-weight: 600;
    color: {COLORS['negro']};
}}
.metric-sub {{
    font-size: 11px;
    color: {COLORS['gris_texto']};
    margin-top: 2px;
}}

/* Section title */
.section-title {{
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: {COLORS['gris_texto']};
    margin-bottom: 10px;
    margin-top: 20px;
    border-bottom: 0.5px solid {COLORS['arena']};
    padding-bottom: 6px;
}}

/* Badges */
.badge {{
    display: inline-block;
    padding: 2px 9px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    font-family: 'Raleway', sans-serif;
}}
.badge-a  {{ background: #d4edda; color: #155724; }}
.badge-b  {{ background: #cce5ff; color: #004085; }}
.badge-c  {{ background: #fff3cd; color: #856404; }}
.badge-d  {{ background: #f8d7da; color: #721c24; }}
.badge-activo  {{ background: #d4edda; color: #155724; }}
.badge-nuevo   {{ background: #cce5ff; color: #004085; }}
.badge-sale    {{ background: #fce4ec; color: #880e4f; }}
.badge-borrador {{ background: {COLORS['verde_agua']}; color: {COLORS['gris_texto']}; }}
.badge-baja    {{ background: #f8d7da; color: #721c24; }}

/* Alert badges */
.alert-quiebre  {{ background: #f8d7da; color: #721c24; padding: 3px 8px; border-radius: 4px; font-size: 11px; }}
.alert-urgente  {{ background: #fff3cd; color: #856404; padding: 3px 8px; border-radius: 4px; font-size: 11px; }}
.alert-proximo  {{ background: #cce5ff; color: #004085; padding: 3px 8px; border-radius: 4px; font-size: 11px; }}
.alert-aceleracion {{ background: #d4edda; color: #155724; padding: 3px 8px; border-radius: 4px; font-size: 11px; }}

/* Upload zones */
.upload-ok {{
    background: #d4edda;
    border: 1px dashed #27AE60;
    border-radius: 8px;
    padding: 14px;
    text-align: center;
    font-size: 13px;
    color: #155724;
}}
.upload-pending {{
    background: {COLORS['verde_agua']};
    border: 1px dashed {COLORS['arena']};
    border-radius: 8px;
    padding: 14px;
    text-align: center;
    font-size: 13px;
    color: {COLORS['gris_texto']};
}}

/* Provider pill buttons */
.prov-pill {{
    display: inline-block;
    padding: 5px 14px;
    border-radius: 20px;
    border: 0.5px solid {COLORS['arena']};
    background: {COLORS['blanco']};
    color: {COLORS['gris_texto']};
    font-size: 12px;
    cursor: pointer;
    margin: 3px;
    font-family: 'Raleway', sans-serif;
}}
.prov-pill-active {{
    background: {COLORS['negro']};
    color: {COLORS['arena']};
    border-color: {COLORS['negro']};
}}

/* Table styling */
.andina-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    font-family: 'Raleway', sans-serif;
}}
.andina-table th {{
    background: {COLORS['verde_agua']};
    padding: 8px 10px;
    text-align: left;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: {COLORS['gris_texto']};
    border-bottom: 0.5px solid {COLORS['arena']};
}}
.andina-table td {{
    padding: 9px 10px;
    border-bottom: 0.5px solid {COLORS['arena']};
    vertical-align: middle;
}}
.andina-table tr:hover td {{
    background: {COLORS['verde_agua']};
}}

/* Buttons */
.andina-btn {{
    background: {COLORS['negro']};
    color: {COLORS['arena']};
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    font-family: 'Raleway', sans-serif;
    font-size: 13px;
    cursor: pointer;
    letter-spacing: 0.5px;
}}
.andina-btn-outline {{
    background: transparent;
    color: {COLORS['negro']};
    border: 0.5px solid {COLORS['negro']};
    padding: 9px 18px;
    border-radius: 6px;
    font-family: 'Raleway', sans-serif;
    font-size: 13px;
    cursor: pointer;
}}

/* Pedido total bar */
.pedido-total {{
    background: {COLORS['negro']};
    color: {COLORS['arena']};
    border-radius: 8px;
    padding: 14px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 14px;
}}

/* YoY tag */
.tag-yoy-up {{ background: #d4edda; color: #155724; padding: 2px 7px; border-radius: 3px; font-size: 11px; font-family: 'Raleway'; }}
.tag-yoy-dn {{ background: #f8d7da; color: #721c24; padding: 2px 7px; border-radius: 3px; font-size: 11px; font-family: 'Raleway'; }}
.tag-neutral {{ background: {COLORS['verde_agua']}; color: {COLORS['gris_texto']}; padding: 2px 7px; border-radius: 3px; font-size: 11px; font-family: 'Raleway'; }}

/* Streamlit overrides */
div[data-testid="stButton"] > button {{
    font-family: 'Raleway', sans-serif;
    border-radius: 6px;
}}
div[data-testid="stSelectbox"] label,
div[data-testid="stNumberInput"] label,
div[data-testid="stTextInput"] label {{
    font-family: 'Raleway', sans-serif;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: {COLORS['gris_texto']};
}}
div[data-testid="stDataFrame"] {{
    border: 0.5px solid {COLORS['arena']};
    border-radius: 8px;
}}
.stTabs [data-baseweb="tab-list"] {{
    gap: 8px;
    background: transparent;
}}
.stTabs [data-baseweb="tab"] {{
    font-family: 'Raleway', sans-serif;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: {COLORS['gris_texto']};
    background: {COLORS['blanco']};
    border: 0.5px solid {COLORS['arena']};
    border-radius: 6px;
    padding: 6px 16px;
}}
.stTabs [aria-selected="true"] {{
    background: {COLORS['negro']} !important;
    color: {COLORS['arena']} !important;
    border-color: {COLORS['negro']} !important;
}}
</style>
"""

def render_header(subtitle="Sistema de Pedidos"):
    import streamlit as st
    st.markdown(f"""
    <div class="andina-header">
        <div>
            <div class="andina-logo">Andina</div>
            <div class="andina-subtitle">Tienda de Tesoros</div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:13px; color:{COLORS['gris_texto']}; font-family:'Raleway';">{subtitle}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def section_title(text):
    import streamlit as st
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)
