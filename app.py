import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Pixel Thread - Gestión de Pedidos",
    page_icon="🧵",
    layout="wide"
)

# --- CSS PERSONALIZADO ---
st.markdown("""
<style>
    /* 1. Ocultar la barra superior (Menú, icono GitHub, Fork) */
    header[data-testid="stHeader"], 
    [data-testid="stToolbar"], 
    #MainMenu {
        visibility: hidden !important;
        display: none !important;
    }

    /* 2. Ocultar el pie de página (Marca Streamlit, status widget) */
    footer, 
    [data-testid="stStatusWidget"], 
    [data-testid="stDecoration"],
    .stAppViewFooter {
        visibility: hidden !important;
        display: none !important;
    }

    /* Ajuste del espacio superior al ocultar el header */
    .block-container {
        padding-top: 1rem !important;
    }
</style>
""", unsafe_allow_html=True)


# --- FUNCIONES AUXILIARES ---
def limpiar_lista_archivos(lista_archivos):
    if not lista_archivos:
        return []
    if isinstance(lista_archivos, list):
        return lista_archivos
    return [lista_archivos]

def render_estado_badge(estado):
    if estado == "Completado":
        st.markdown("**Estado:** Completado 🔵")
    elif estado == "En Proceso":
        st.markdown("**Estado:** En Proceso 🟢")
    else:
        st.markdown(f"**Estado:** {estado} 🔴")


# --- INTERFAZ PRINCIPAL ---
st.title("🧵 Pixel Thread - Panel de Control")

# Ejemplo de estructura de datos / consulta
mis_pedidos = st.session_state.get('pedidos', [
    {
        'id': 1,
        'nombre_proyecto': 'prueba nombre logo 2',
        'producto': 'GORRA',
        'ubicacion': 'TRASERO',
        'estilo': 'N/A',
        'estado': 'Completado',
        'archivos_finales': [
            {'nombre': 'PIXEL THREAD.png', 'url': 'https://via.placeholder.com/150'}
        ]
    }
])

# Pestañas principales
tab_pendientes, tab_completados = st.tabs(["⏳ Pedidos Pendientes", "✅ Pedidos Completados"])

with tab_pendientes:
    st.subheader("📋 Pedidos en Proceso y Cola")
    pedidos_pendientes = [p for p in mis_pedidos if p.get('estado') != "Completado"]
    if pedidos_pendientes:
        for p in pedidos_pendientes:
            st.write(p)
    else:
        st.info("No hay pedidos pendientes en este momento.")

with tab_completados:
    st.subheader("🎉 Historial de Pedidos Listos")
    pedidos_terminados = [p for p in mis_pedidos if p.get('estado') == "Completado"]

    if pedidos_terminados:
        cols = st.columns(4)
        for i, p in enumerate(pedidos_terminados):
            with cols[i % 4]:
                with st.container(border=True):
                    st.markdown(f"**🧵 Proyecto:** {p.get('nombre_proyecto', 'N/A')}")
                    st.markdown(f"**📦 Producto:** {p.get('producto', 'N/A')}")
                    st.markdown(f"**📍 Ubicación:** {p.get('ubicacion', 'N/A')}")
                    st.markdown(f"**🎨 Estilo:** {p.get('estilo', 'N/A')}")
                    render_estado_badge(p.get('estado'))

                    # Obtención de archivos listos
                    archivos_finales = limpiar_lista_archivos(p.get('archivos_finales', []))
                    if archivos_finales:
                        st.markdown("✨ **Archivos Entregados:**")
                        for idx_f, af in enumerate(archivos_finales):
                            nom_f = af.get('nombre', f'archivo_{idx_f+1}')
                            url_f = af.get('url') or af.get('data', '')
                            if url_f:
                                if nom_f.lower().endswith(('png', 'jpg', 'jpeg', 'webp')):
                                    st.image(url_f, width=120, caption=nom_f)
                                
                                # Botón de descarga legible
                                st.markdown(
                                    f"""
                                    <a href="{url_f}" target="_blank" download="{nom_f}" style="
                                        display: inline-block;
                                        background-color: #00ffcc;
                                        color: #000000;
                                        padding: 8px 14px;
                                        text-decoration: none;
                                        border-radius: 6px;
                                        font-weight: bold;
                                        font-size: 14px;
                                        margin-top: 5px;
                                        box-shadow: 0 0 10px rgba(0, 255, 204, 0.4);
                                    ">📥 DESCARGAR {nom_f}</a>
                                    """, 
                                    unsafe_allow_html=True
                                )
                    else:
                        st.warning("⚠️ El pedido está completado, pero no hay archivos cargados aún.")
    else:
        st.info("Aún no tienes pedidos completados.")
