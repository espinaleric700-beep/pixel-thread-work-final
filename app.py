import streamlit as st

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Pixel Thread | Pro",
    page_icon="🧵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS PERSONALIZADO Y OCULTACIÓN DE BARRAS/BOTONES ---
st.markdown("""
<style>
    /* 1. Ocultar la barra superior completa (menú de tres puntos, GitHub, etc.) */
    header, [data-testid="stHeader"], .stAppToolbar {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }

    /* 2. Ocultar el visor flotante / avatar y barquito (Streamlit Cloud Toolbar) */
    [data-testid="stStatusWidget"],
    [data-testid="stToolbar"],
    div[class*="stAppViewerToolbar"],
    div[class*="viewerBadge"],
    div[data-testid="stDecoration"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }

    :root {
        --primary: #00ffcc;
    }
    .stApp {
        background: radial-gradient(circle at 50% 50%, #1a0033 0%, #050505 100%);
        background-attachment: fixed;
        color: #ffffff;
    }
    .block-container {
        max-width: 100% !important;
        padding-left: 2rem;
        padding-right: 2rem;
        padding-top: 0rem !important;
    }
    
    html, body, [data-testid="stMarkdownContainer"], p, span, label {
        font-size: 16px !important;
    }
    
    div[data-testid="stExpander"] {
        background: rgba(15, 15, 25, 0.7) !important;
        border: 1px solid rgba(0, 255, 204, 0.3) !important;
        border-radius: 10px !important;
        padding: 8px;
    }
    
    div.stButton > button {
        background: transparent !important;
        color: var(--primary) !important;
        border: 1px solid var(--primary) !important;
        border-radius: 6px !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase;
        font-weight: bold;
        font-size: 14px !important;
        padding: 6px 12px;
    }
    div.stButton > button:hover {
        background: var(--primary) !important;
        color: black !important;
        box-shadow: 0 0 15px var(--primary) !important;
        transform: translateY(-2px);
    }
    
    h1 { color: var(--primary) !important; font-size: 2.5rem !important; letter-spacing: 2px; }
    h2 { color: var(--primary) !important; font-size: 1.8rem !important; }
    h3 { color: var(--primary) !important; font-size: 1.3rem !important; }

    .dot-red {
        height: 10px; width: 10px; background-color: #ff4b4b; border-radius: 50%;
        display: inline-block; margin-left: 6px; box-shadow: 0 0 8px #ff4b4b; vertical-align: middle;
    }
    .dot-green {
        height: 10px; width: 10px; background-color: #00ff80; border-radius: 50%;
        display: inline-block; margin-left: 6px; box-shadow: 0 0 8px #00ff80; vertical-align: middle;
    }
    .dot-blue {
        height: 10px; width: 10px; background-color: #00bfff; border-radius: 50%;
        display: inline-block; margin-left: 6px; box-shadow: 0 0 8px #00bfff; vertical-align: middle;
    }
</style>
""", unsafe_allow_html=True)
