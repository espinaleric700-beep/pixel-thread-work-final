import streamlit as st

# --- ENCABEZADO SUPERIOR / MENÚ DE IDENTIFICACIÓN ---
col_head1, col_head2 = st.columns([3, 1])

with col_head1:
    st.title("⚡ PIXEL THREAD")

with col_head2:
    with st.popover("⚙️ Menú"):
        st.markdown("### Identificación")
        
        # Al envolver los inputs dentro de st.form, el popover colapsa automáticamente al enviar
        with st.form("form_login_menu", border=False):
            nuevo_usuario = st.text_input(
                "Usuario / ID Cliente:", 
                value=st.session_state.get("user", ""), 
                key="input_user_menu"
            )
            btn_login = st.form_submit_button("🚀 INICIAR SESIÓN", use_container_width=True)
            
            if btn_login:
                usr = nuevo_usuario.strip()
                if not usr:
                    st.error("⚠️ Ingresa un usuario válido.")
                elif existe_usuario(usr):  # Tu función de verificación de usuario
                    st.session_state.user = usr
                    st.session_state.mensaje_exito = f"👋 ¡Bienvenido/a {usr}!"
                    
                    # Actualiza la URL o ejecuta st.rerun() para refrescar la interfaz
                    if "actualizar_url" in globals():
                        actualizar_url(st.session_state.get("modo_vista", "Cliente"), usr)
                    else:
                        st.rerun()
                else:
                    st.error("❌ El usuario no existe en la base de datos.")

        st.markdown("---")
        st.markdown("### Navegación")
        
        if st.button("👤 PANEL CLIENTE", use_container_width=True, key="btn_nav_cliente"): 
            st.session_state.modo_vista = "Cliente"
            if "actualizar_url" in globals():
                actualizar_url("Cliente", st.session_state.get("user", ""))
            else:
                st.rerun()
            
        if st.button("🛠️ PANEL ADMIN", use_container_width=True, key="btn_nav_admin"): 
            usuario_actual = st.session_state.get("user", "").strip()
            # Valida los permisos si tienes la lista ADMINS_AUTORIZADOS
            admins = ADMINS_AUTORIZADOS if "ADMINS_AUTORIZADOS" in globals() else []
            if not admins or usuario_actual.lower() in [a.lower() for a in admins]:
                st.session_state.modo_vista = "Admin"
                if "actualizar_url" in globals():
                    actualizar_url("Admin", usuario_actual)
                else:
                    st.rerun()
            else:
                st.error("❌ Sin permisos de administrador.")
