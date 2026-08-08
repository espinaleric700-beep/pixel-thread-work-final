import streamlit as st

# Configuración de página
st.set_page_config(page_title="PIXEL THREAD", page_icon="⚡", layout="wide")

# --- INICIALIZACIÓN DE SESSION STATE ---
if "user" not in st.session_state:
    st.session_state.user = ""

if "modo_vista" not in st.session_state:
    st.session_state.modo_vista = "Cliente"

if "mensaje_exito" not in st.session_state:
    st.session_state.mensaje_exito = None

# --- ENCABEZADO SUPERIOR / MENÚ ---
col_head1, col_head2 = st.columns([3, 1])

with col_head1:
    st.title("⚡ PIXEL THREAD")

with col_head2:
    with st.popover("⚙️ Menú"):
        st.markdown("### Identificación")
        
        with st.form("form_login_menu", border=False):
            nuevo_usuario = st.text_input(
                "Usuario / ID Cliente:", 
                value=st.session_state.user, 
                key="input_user_menu"
            )
            btn_login = st.form_submit_button("🚀 INICIAR SESIÓN", use_container_width=True)
            
            if btn_login:
                usr = nuevo_usuario.strip()
                if not usr:
                    st.error("⚠️ Ingresa un usuario válido.")
                elif existe_usuario(usr):  # Asegúrate de tener definidos tus helpers
                    st.session_state.user = usr
                    st.session_state.mensaje_exito = f"👋 ¡Bienvenido/a {usr}!"
                    st.rerun()
                else:
                    st.error("❌ El usuario no existe en la base de datos.")

        st.markdown("---")
        st.markdown("### Navegación")
        
        if st.button("👤 PANEL CLIENTE", use_container_width=True, key="btn_nav_cliente"): 
            st.session_state.modo_vista = "Cliente"
            st.rerun()
            
        if st.button("🛠️ PANEL ADMIN", use_container_width=True, key="btn_nav_admin"): 
            usuario_actual = st.session_state.user.strip()
            admins = ADMINS_AUTORIZADOS if "ADMINS_AUTORIZADOS" in globals() else []
            if not admins or usuario_actual.lower() in [a.lower() for a in admins]:
                st.session_state.modo_vista = "Admin"
                st.rerun()
            else:
                st.error("❌ Sin permisos de administrador.")

# --- MOSTRAR MENSAJE DE ÉXITO SI EXISTE ---
if st.session_state.mensaje_exito:
    st.success(st.session_state.mensaje_exito)
    st.session_state.mensaje_exito = None

# --- CONTROL DE FLUJO Y RENDERIZADO PRINCIPAL ---
# 1. Si no hay usuario en sesión, mostrar pantalla de inicio / bienvenida
if not st.session_state.user:
    st.info("👋 Bienvenid@ a **PIXEL THREAD**. Por favor, inicia sesión desde el menú superior **⚙️ Menú** para ver tus órdenes.")
    
    st.subheader("🔑 Acceso Rápido")
    with st.form("form_login_principal"):
        usr_input = st.text_input("Ingresa tu ID Cliente / Usuario:")
        submit_main = st.form_submit_button("Iniciar Sesión")
        if submit_main:
            if usr_input.strip() and existe_usuario(usr_input.strip()):
                st.session_state.user = usr_input.strip()
                st.rerun()
            else:
                st.error("Usuario no encontrado.")

# 2. Si hay usuario autenticado, renderizar según la vista seleccionada
else:
    if st.session_state.modo_vista == "Admin":
        # Llamada a tu función/módulo del Panel de Admin
        if "render_panel_admin" in globals():
            render_panel_admin()
        else:
            st.subheader("🛠️ Panel de Administración")
            # Agrega aquí el contenido de tu panel de administrador
            st.write(f"Bienvenido Administrador: {st.session_state.user}")

    else:
        # Llamada a tu función/módulo del Panel de Cliente
        if "render_panel_cliente" in globals():
            render_panel_cliente()
        else:
            st.subheader(f"📦 Panel de Cliente - {st.session_state.user}")
            # Agrega aquí el formulario para enviar logo / consultar órdenes
