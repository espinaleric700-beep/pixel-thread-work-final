import streamlit as st
# Si usas Supabase o Firebase para la base de datos, mantén sus imports correspondientes aquí
# import supabase ...

# 1. Configuración de la página
st.set_page_config(
    page_title="Pixel Thread - Gestión de Pedidos",
    page_icon="🧵",
    layout="wide"
)

# 2. Ocultar menús nativos y header/footer de Streamlit con CSS
st.markdown("""
<style>
    /* Ocultar barra superior y menús de Streamlit */
    header[data-testid="stHeader"], 
    [data-testid="stToolbar"], 
    #MainMenu {
        visibility: hidden !important;
        display: none !important;
    }

    /* Ocultar pie de página y widgets */
    footer, 
    [data-testid="stStatusWidget"], 
    [data-testid="stDecoration"],
    .stAppViewFooter {
        visibility: hidden !important;
        display: none !important;
    }

    /* Ajuste de margen superior */
    .block-container {
        padding-top: 1.5rem !important;
    }
</style>
""", unsafe_allow_html=True)


# 3. Funciones auxiliares
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

# Función para cargar pedidos reales desde tu base de datos
def obtener_pedidos_usuario(usuario_id):
    # Sustituye esta función por tu consulta real (Supabase / Firebase)
    # Ejemplo: return supabase.table('pedidos').select('*').eq('usuario', usuario_id).execute().data
    return st.session_state.get("mis_pedidos", [])


# 4. Control de sesión y búsqueda de usuario
st.title("🧵 Pixel Thread - Panel de Control")

col_input, col_btn = st.columns([4, 1])
with col_input:
    usuario = st.text_input("Ingresa tu Nombre o ID de Usuario:", key="input_usuario_id")
with col_btn:
    st.write("") # Espaciador
    st.write("")
    buscar = st.button("🔍 INGRESAR", use_container_width=True)

if usuario:
    st.success(f"👤 Hola, **{usuario}**")
    
    # Obtener pedidos reales de la base de datos
    mis_pedidos = obtener_pedidos_usuario(usuario)

    # Acordeón para nuevo pedido
    with st.expander("➕ Enviar Nuevo Pedido"):
        st.write("Formulario para enviar nuevo logo/archivo...")
        # Inserta aquí tus campos de envío (nombre_proyecto, producto, ubicación, etc.)

    # Visualización de pedidos en pestañas
    tab_pendientes, tab_completados = st.tabs(["⏳ Pedidos Pendientes", "✅ Pedidos Completados"])

    with tab_pendientes:
        st.subheader("📋 Pedidos en Proceso y Cola")
        pedidos_pendientes = [p for p in mis_pedidos if p.get('estado') != "Completado"]

        if pedidos_pendientes:
            cols = st.columns(2)
            for i, p in enumerate(pedidos_pendientes):
                with cols[i % 2]:
                    with st.container(border=True):
                        st.markdown(f"**📊 Turno en Cola:** #{i+1}")
                        st.markdown(f"**🧵 Proyecto:** {p.get('nombre_proyecto', 'N/A')}")
                        st.markdown(f"**📦 Producto:** {p.get('producto', 'N/A')}")
                        st.markdown(f"**📍 Ubicación:** {p.get('ubicacion', 'N/A')}")
                        st.markdown(f"**🎨 Estilo:** {p.get('estilo', 'PLANO')}")
                        render_estado_badge(p.get('estado', 'Pendiente'))
                        if p.get('comentario'):
                            st.caption(f"📝 Nota: {p.get('comentario')}")
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
                        st.markdown(f"**🎨 Estilo:** {p.get('estilo', 'PLANO')}")
                        render_estado_badge("Completado")

                        archivos_finales = limpiar_lista_archivos(p.get('archivos_finales', []))
                        if archivos_finales:
                            st.markdown("✨ **Archivos Entregados:**")
                            for idx_f, af in enumerate(archivos_finales):
                                nom_f = af.get('nombre', f'archivo_{idx_f+1}')
                                url_f = af.get('url') or af.get('data', '')
                                if url_f:
                                    if nom_f.lower().endswith(('png', 'jpg', 'jpeg', 'webp')):
                                        st.image(url_f, width=120, caption=nom_f)
                                    
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
else:
    st.warning("Por favor ingresa tu nombre o ID de usuario para consultar tus pedidos.")
