import streamlit as st
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import cloudinary
import cloudinary.uploader

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Pixel Thread | Pro", layout="wide")

# --- CONFIGURACIÓN DE CLOUDINARY ---
cloudinary.config(
    cloud_name = "oik5ivju",
    api_key = "535459971576711",
    api_secret = "J8iAbx6U3AV1_uQJiX3CwCeSR8A",
    secure = True
)

def subir_a_cloudinary(file_obj, nombre_archivo):
    """
    Sube archivos de cualquier tamaño a Cloudinary.
    Soporta imágenes (.png, .jpg) y archivos de bordado (.emb, .dst, .pes, etc.).
    """
    try:
        extension = nombre_archivo.split('.')[-1].lower()
        resource_type = "image" if extension in ["png", "jpg", "jpeg", "webp"] else "raw"
        
        response = cloudinary.uploader.upload(
            file_obj.getvalue(),
            resource_type=resource_type,
            public_id=f"pixel_thread/{nombre_archivo}"
        )
        return response.get("secure_url")
    except Exception as e:
        st.error(f"Error al subir a Cloudinary: {e}")
        return None

# --- CSS PERSONALIZADO ---
st.markdown("""
<style>
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
        padding-top: 1.5rem;
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

# --- INICIALIZACIÓN DE FIREBASE ---
@st.cache_resource
def init_fb():
    if not firebase_admin._apps:
        cred_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_fb()

# --- FUNCIONES AUXILIARES ---
def recalcular_turnos():
    try:
        docs = list(db.collection("pedidos_bordado").order_by("timestamp").stream())
        turno_actual = 1
        for doc in docs:
            data = doc.to_dict()
            estado = data.get("estado", "Pendiente")
            if estado != "Completado":
                db.collection("pedidos_bordado").document(doc.id).update({"turno": turno_actual})
                turno_actual += 1
            else:
                db.collection("pedidos_bordado").document(doc.id).update({"turno": "N/A"})
    except Exception:
        pass

def obtener_uso_firebase():
    try:
        pedidos = list(db.collection("pedidos_bordado").stream())
        clientes = list(db.collection("usuarios_perfil").stream())
        total_docs = len(pedidos) + len(clientes)
        
        limite_lecturas = 50000
        lecturas_actuales = min(total_docs * 5, limite_lecturas) 
        porcentaje_uso = min(float(lecturas_actuales) / limite_lecturas * 100, 100.0)
        
        return {
            "total_docs": total_docs,
            "lecturas": lecturas_actuales,
            "limite_lecturas": limite_lecturas,
            "porcentaje": porcentaje_uso
        }
    except Exception:
        return {"total_docs": 0, "lecturas": 45000, "limite_lecturas": 50000, "porcentaje": 90.0}

def limpiar_lista_archivos(raw_data):
    lista_limpia = []
    if not isinstance(raw_data, list):
        return []
    for item in raw_data:
        if isinstance(item, list):
            lista_limpia.extend(limpiar_lista_archivos(item))
        elif isinstance(item, dict) and "nombre" in item and ("url" in item or "data" in item):
            lista_limpia.append(item)
    return lista_limpia

def vaciar_pedidos():
    """Elimina únicamente todos los documentos de la colección de pedidos."""
    docs = list(db.collection("pedidos_bordado").stream())
    for doc in docs:
        db.collection("pedidos_bordado").document(doc.id).delete()
    return len(docs)

# --- GESTIÓN DE ESTADOS Y URL ---
params = st.query_params
if "modo_vista" not in st.session_state: 
    st.session_state.modo_vista = params.get("seccion", "Cliente")
if "user" not in st.session_state: 
    st.session_state.user = params.get("user", "")
if "expandir_nuevo_pedido" not in st.session_state: 
    st.session_state.expandir_nuevo_pedido = False
if "mensaje_exito" not in st.session_state: 
    st.session_state.mensaje_exito = ""
if "form_version" not in st.session_state: 
    st.session_state.form_version = 0

def actualizar_url(vista, user):
    st.session_state.modo_vista = vista
    st.session_state.user = user
    st.query_params["seccion"] = vista
    st.query_params["user"] = user
    st.rerun()

ADMINS_AUTORIZADOS = ["Pixel2580", "eric"]

def render_estado_badge(estado):
    if estado == "Pendiente":
        st.markdown("**Estado:** Pendiente <span class='dot-red'></span>", unsafe_allow_html=True)
    elif estado == "En Proceso":
        st.markdown("**Estado:** En Proceso <span class='dot-green'></span>", unsafe_allow_html=True)
    else:
        st.markdown("**Estado:** Completado <span class='dot-blue'></span>", unsafe_allow_html=True)

# --- ENCABEZADO SUPERIOR ---
col_head1, col_head2 = st.columns([3, 1])

with col_head1:
    st.title("⚡ PIXEL THREAD")

with col_head2:
    with st.popover("⚙️ Menú"):
        st.markdown("### Navegación")
        if st.button("👤 Panel Cliente", use_container_width=True): 
            actualizar_url("Cliente", st.session_state.user)
        if st.button("🛠️ Panel Admin", use_container_width=True): 
            usuario_actual = st.session_state.user.strip()
            if usuario_actual in ADMINS_AUTORIZADOS:
                actualizar_url("Admin", st.session_state.user)
            else:
                st.error("❌ Sin permisos.")

st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
# VISTA CLIENTE
# =========================================================
@st.fragment(run_every=10)
def renderizar_tablas_cliente(user_clean):
    tab_pendientes, tab_completados = st.tabs(["⏳ Pedidos Pendientes", "✅ Pedidos Completados"])

    todos = list(db.collection("pedidos_bordado").order_by("timestamp").stream())
    mis_pedidos = [p.to_dict() for p in todos if p.to_dict().get("cliente", "").strip().lower() == user_clean]

    with tab_pendientes:
        st.subheader("📋 Pedidos en Proceso")
        pedidos_activos = [p for p in mis_pedidos if p.get('estado') != "Completado"]
        
        if pedidos_activos:
            cols = st.columns(4)
            for i, p in enumerate(pedidos_activos):
                with cols[i % 4]:
                    with st.container(border=True):
                        turno_val = p.get('turno', 'N/A')
                        st.markdown(f"**🔢 Turno en Cola:** `#{turno_val}`")
                        st.markdown(f"**🧵 Proyecto:** {p.get('nombre_proyecto', 'N/A')}")
                        st.markdown(f"**📦 Producto:** {p.get('producto', 'N/A')}")
                        st.markdown(f"**📍 Ubicación:** {p.get('ubicacion', 'N/A')}")
                        st.markdown(f"**🎨 Estilo:** {p.get('estilo', 'N/A')}")
                        render_estado_badge(p.get('estado', 'Pendiente'))
                        if p.get('comentarios'):
                            st.caption(f"📝 Nota: {p.get('comentarios')}")

                        archivos = p.get('archivos', [])
                        if archivos:
                            st.markdown("📁 **Archivos Adjuntos:**")
                            for idx_a, arch_item in enumerate(archivos):
                                nombre_a = arch_item.get('nombre', 'archivo')
                                url_a = arch_item.get('url', '')
                                if url_a:
                                    if nombre_a.lower().endswith(('png', 'jpg', 'jpeg')):
                                        st.image(url_a, width=120, caption=nombre_a)
                                    st.markdown(f"📥 [Descargar {nombre_a}]({url_a})")
        else:
            st.info("No tienes pedidos pendientes activos.")

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
                        render_estado_badge("Completado")

                        archivos_finales = limpiar_lista_archivos(p.get('archivos_finales', []))
                        if archivos_finales:
                            st.markdown("✨ **Archivos Listos para Descarga:**")
                            for idx_f, af in enumerate(archivos_finales):
                                nom_f = af.get('nombre', 'resultado')
                                url_f = af.get('url', '')
                                if url_f:
                                    if nom_f.lower().endswith(('png', 'jpg', 'jpeg')):
                                        st.image(url_f, width=120, caption=nom_f)
                                    st.markdown(f"📥 [Descargar {nom_f}]({url_f})")
        else:
            st.info("Aún no tienes pedidos completados.")

# =========================================================
# VISTA ADMINISTRADOR
# =========================================================
@st.fragment(run_every=10)
def renderizar_panel_admin():
    uso_fb = obtener_uso_firebase()
    porcentaje_uso = uso_fb["porcentaje"]
    
    st.markdown("### 📊 Estado del Plan Firebase")
    col_metrica1, col_metrica2, col_metrica3 = st.columns(3)
    with col_metrica1:
        st.metric(label="Lecturas Diarias", value=f"{uso_fb['lecturas']:,} / {uso_fb['limite_lecturas']:,}")
    with col_metrica2:
        st.metric(label="Porcentaje Utilizado", value=f"{porcentaje_uso:.1f}%")
    with col_metrica3:
        if porcentaje_uso >= 90:
            st.error("⚠️ ¡Límite crítico alcanzado!")
        elif porcentaje_uso > 75:
            st.warning("⚡ Uso elevado del plan gratuito.")
        else:
            st.success("✅ Uso dentro del margen seguro.")
            
    st.progress(min(porcentaje_uso / 100.0, 1.0))
    st.markdown("---")

    tab_admin_pend, tab_admin_comp, tab_admin_clientes = st.tabs([
        "⏳ Pendientes y En Proceso", 
        "✅ Completados / Entregados", 
        "👥 Gestión de Clientes"
    ])

    recalcular_turnos()
    docs = list(db.collection("pedidos_bordado").order_by("timestamp").stream())

    with tab_admin_pend:
        pedidos_activos = [(doc.id, doc.to_dict()) for doc in docs if doc.to_dict().get('estado') != "Completado"]

        if pedidos_activos:
            cols = st.columns(4)
            for i, (doc_id, p) in enumerate(pedidos_activos):
                with cols[i % 4]:
                    with st.container(border=True):
                        turno_val = p.get('turno', 'N/A')
                        st.markdown(f"**🔢 Turno:** `#{turno_val}`")
                        st.markdown(f"**👤 Cliente:** `{p.get('cliente')}`")
                        st.markdown(f"**🧵 Proyecto:** `{p.get('nombre_proyecto', 'N/A')}`")
                        st.markdown(f"**📦 Producto:** {p.get('producto', 'N/A')}")
                        st.markdown(f"**📍 Ubicación:** {p.get('ubicacion', 'N/A')}")
                        st.markdown(f"**🎨 Estilo:** {p.get('estilo', 'N/A')}")
                        
                        estado_actual = p.get('estado', 'Pendiente')
                        render_estado_badge(estado_actual)
                        
                        if p.get('comentarios'):
                            st.caption(f"📝 Comentarios: {p.get('comentarios')}")
                        
                        if estado_actual == "Pendiente":
                            if st.button("🔄 En Proceso", key=f"btn_proceso_{doc_id}", use_container_width=True):
                                db.collection("pedidos_bordado").document(doc_id).update({"estado": "En Proceso"})
                                recalcular_turnos()
                                st.rerun()
                        else:
                            if st.button("🔄 Pendiente", key=f"btn_pendiente_{doc_id}", use_container_width=True):
                                db.collection("pedidos_bordado").document(doc_id).update({"estado": "Pendiente"})
                                recalcular_turnos()
                                st.rerun()

                        archivos_cliente = p.get('archivos', [])
                        if archivos_cliente:
                            st.markdown("📁 **Archivos del Cliente:**")
                            for idx_ac, ac in enumerate(archivos_cliente):
                                nom_ac = ac.get('nombre', 'archivo')
                                url_ac = ac.get('url', '')
                                if url_ac:
                                    if nom_ac.lower().endswith(('png', 'jpg', 'jpeg')):
                                        st.image(url_ac, width=100, caption=nom_ac)
                                    st.markdown(f"📥 [Descargar {nom_ac}]({url_ac})")

                        with st.expander("📤 Entregar Archivos Finales"):
                            lista_finales = limpiar_lista_archivos(p.get('archivos_finales', []))
                            
                            if lista_finales:
                                st.markdown("**✨ Ya subidos:**")
                                for idx_f, af in enumerate(lista_finales):
                                    c_nom, c_btn = st.columns([4, 1])
                                    with c_nom:
                                        st.caption(f"📄 {af.get('nombre', 'archivo')}")
                                    with c_btn:
                                        if st.button("❌", key=f"del_arch_pend_{doc_id}_{idx_f}", help="Eliminar este archivo"):
                                            lista_finales.pop(idx_f)
                                            db.collection("pedidos_bordado").document(doc_id).update({"archivos_finales": lista_finales})
                                            st.rerun()
                                            
                            st.markdown("**➕ Seleccionar entregables (.EMB, .DST, .PES, etc):**")
                            archivos_entregables = st.file_uploader(
                                "Seleccionar archivos:", 
                                type=["dst", "emb", "pes", "png", "jpg", "pdf"],
                                accept_multiple_files=True, 
                                key=f"up_admin_{doc_id}"
                            )
                            if st.button("🚀 SUBIR Y COMPLETAR", key=f"btn_comp_{doc_id}", use_container_width=True):
                                if archivos_entregables:
                                    try:
                                        status_subida = st.empty()
                                        total_archivos = len(archivos_entregables)
                                        timestamp_num = int(datetime.now().timestamp())
                                        
                                        for idx, af in enumerate(archivos_entregables, start=1):
                                            status_subida.info(f"⏳ Subiendo {af.name} ({idx}/{total_archivos})...")
                                            nombre_unico = f"entrega_{doc_id}_{timestamp_num}_{af.name}"
                                            url_publica = subir_a_cloudinary(af, nombre_unico)
                                            
                                            if url_publica:
                                                lista_finales.append({"nombre": af.name, "url": url_publica})
                                            
                                        db.collection("pedidos_bordado").document(doc_id).update({
                                            "archivos_finales": lista_finales,
                                            "estado": "Completado",
                                            "turno": "N/A"
                                        })
                                        
                                        recalcular_turnos()
                                        status_subida.success("¡Pedido marcado como Completado!")
                                        st.rerun()
                                    except Exception as e:
                                        status_subida.error(f"Error al subir: {e}")
                                else:
                                    st.warning("Adjunta al menos un archivo.")

                        if st.button("🗑️ Eliminar Pedido", key=f"mob_del_{doc_id}", use_container_width=True):
                            db.collection("pedidos_bordado").document(doc_id).delete()
                            recalcular_turnos()
                            st.rerun()
        else:
            st.info("🎉 No hay pedidos pendientes de revisión.")

    with tab_admin_comp:
        pedidos_completados_admin = [
            (doc.id, doc.to_dict()) 
            for doc in docs 
            if doc.to_dict().get('estado') == "Completado"
        ]

        if pedidos_completados_admin:
            cols = st.columns(4)
            for i, (doc_id, p) in enumerate(pedidos_completados_admin):
                with cols[i % 4]:
                    with st.container(border=True):
                        st.markdown(f"**👤 {p.get('cliente')}**")
                        st.markdown(f"**🧵 {p.get('nombre_proyecto', 'N/A')}**")
                        st.markdown(f"**📦 Producto:** {p.get('producto', 'N/A')}")
                        st.markdown(f"**📍 Ubicación:** {p.get('ubicacion', 'N/A')}")
                        st.markdown(f"**🎨 Estilo:** {p.get('estilo', 'N/A')}")
                        render_estado_badge("Completado")
                        
                        if st.button("🔄 Marcar como Pendiente", key=f"btn_regresar_pend_{doc_id}", use_container_width=True):
                            db.collection("pedidos_bordado").document(doc_id).update({"estado": "Pendiente"})
                            recalcular_turnos()
                            st.rerun()
                        
                        with st.expander("📤 Archivos Entregados"):
                            lista_finales = limpiar_lista_archivos(p.get('archivos_finales', []))
                            
                            if lista_finales:
                                st.markdown("**✨ Archivos enviados:**")
                                for idx_f, af in enumerate(lista_finales):
                                    c_nom, c_btn = st.columns([4, 1])
                                    with c_nom:
                                        st.caption(f"📄 {af.get('nombre', 'archivo')}")
                                    with c_btn:
                                        if st.button("❌", key=f"del_arch_comp_{doc_id}_{idx_f}", help="Eliminar este archivo"):
                                            lista_finales.pop(idx_f)
                                            db.collection("pedidos_bordado").document(doc_id).update({"archivos_finales": lista_finales})
                                            st.rerun()
                                            
                            st.markdown("**➕ Agregar más entregables:**")
                            archivos_extra = st.file_uploader(
                                "Seleccionar archivos:", 
                                type=["dst", "emb", "pes", "png", "jpg", "pdf"],
                                accept_multiple_files=True, 
                                key=f"up_admin_comp_{doc_id}"
                            )
                            if st.button("🚀 SUBIR ARCHIVOS EXTRA", key=f"btn_comp_extra_{doc_id}", use_container_width=True):
                                if archivos_extra:
                                    try:
                                        status_subida = st.empty()
                                        timestamp_num = int(datetime.now().timestamp())
                                        for idx, af in enumerate(archivos_extra, start=1):
                                            status_subida.info(f"⏳ Subiendo {af.name}...")
                                            nombre_unico = f"entrega_extra_{doc_id}_{timestamp_num}_{af.name}"
                                            url_pub = subir_a_cloudinary(af, nombre_unico)
                                            if url_pub:
                                                lista_finales.append({"nombre": af.name, "url": url_pub})
                                            
                                        db.collection("pedidos_bordado").document(doc_id).update({
                                            "archivos_finales": lista_finales
                                        })
                                        status_subida.success("¡Archivos agregados!")
                                        st.rerun()
                                    except Exception as e:
                                        status_subida.error(f"Error al subir: {e}")
                                else:
                                    st.warning("Selecciona al menos un archivo.")

                        if st.button("🗑️ Eliminar Pedido", key=f"mob_del_comp_{doc_id}", use_container_width=True):
                            db.collection("pedidos_bordado").document(doc_id).delete()
                            recalcular_turnos()
                            st.rerun()

    with tab_admin_clientes:
        st.subheader("👥 Gestión de Clientes")

        with st.expander("➕ Registrar Nuevo Cliente / Usuario", expanded=False):
            with st.form("form_nuevo_cliente", clear_on_submit=True):
                nuevo_id = st.text_input("ID o Usuario único (ej: cliente_01):").strip().lower()
                nuevo_nombre = st.text_input("Nombre Completo del Cliente:").strip()
                logo_file = st.file_uploader("Logo del Cliente (Opcional):", type=["png", "jpg", "jpeg"])
                
                btn_registrar = st.form_submit_button("💾 GUARDAR CLIENTE")
                
                if btn_registrar:
                    if not nuevo_id or not nuevo_nombre:
                        st.warning("⚠️ Debes ingresar un ID y un Nombre de cliente.")
                    else:
                        try:
                            logo_url = None
                            if logo_file:
                                logo_url = subir_a_cloudinary(logo_file, f"logo_{nuevo_id}_{logo_file.name}")
                            
                            db.collection("usuarios_perfil").document(nuevo_id).set({
                                "nombre_usuario": nuevo_nombre,
                                "logo_url": logo_url,
                                "creado_en": datetime.now()
                            }, merge=True)
                            
                            st.success(f"✅ Cliente '{nuevo_nombre}' ({nuevo_id}) registrado correctamente.")
                            st.rerun()
                        except Exception as err:
                            st.error(f"Error al guardar cliente: {err}")

        # --- SECCIÓN PARA VACIAR SOLAMENTE LOS PEDIDOS ---
        with st.expander("⚠️ ELIMINAR PEDIDOS (Conservar Clientes)", expanded=False):
            st.warning("Esta opción eliminará TODOS los pedidos y sus archivos de la base de datos para liberar espacio. Los perfiles de clientes SE MANTENDRÁN intactos.")
            confirmacion = st.checkbox("Entiendo que se borrará el historial completo de pedidos.")
            if st.button("🔥 ELIMINAR TODOS LOS PEDIDOS", use_container_width=True):
                if confirmacion:
                    try:
                        cant_pedidos = vaciar_pedidos()
                        st.success(f"✅ Se eliminaron {cant_pedidos} pedidos correctamente. Los perfiles de clientes se han conservado.")
                        st.rerun()
                    except Exception as err_vaciar:
                        st.error(f"Error al eliminar pedidos: {err_vaciar}")
                else:
                    st.warning("Debes marcar la casilla de confirmación para proceder.")

        st.markdown("---")

        clientes_docs = list(db.collection("usuarios_perfil").stream())
        if clientes_docs:
            cols_c = st.columns(3)
            for i, cdoc in enumerate(clientes_docs):
                cdata = cdoc.to_dict()
                cid = cdoc.id
                cnombre = cdata.get('nombre_usuario', 'Sin Nombre')
                clogo = cdata.get('logo_url') or cdata.get('logo_b64')

                with cols_c[i % 3]:
                    with st.container(border=True):
                        col_img, col_txt = st.columns([1, 3])
                        with col_img:
                            if clogo:
                                try:
                                    st.image(clogo, width=50)
                                except Exception:
                                    st.markdown("👤")
                            else:
                                st.markdown("👤")
                        
                        with col_txt:
                            st.markdown(f"**{cnombre}**")
                            st.caption(f"ID: `{cid}`")

                        if st.button("🗑️ Eliminar Cliente", key=f"del_cli_{cid}", use_container_width=True):
                            db.collection("usuarios_perfil").document(cid).delete()
                            st.success(f"Cliente {cid} eliminado.")
                            st.rerun()
        else:
            st.info("No hay perfiles de clientes registrados.")

# =========================================================
# LÓGICA PRINCIPAL (SELECCIÓN DE VISTA)
# =========================================================
if st.session_state.modo_vista == "Cliente":
    col_user_1, col_user_2 = st.columns([3, 1], vertical_alignment="bottom")

    with col_user_1:
        user_input = st.text_input("Ingresa tu Nombre o ID de Usuario:", value=st.session_state.user)

    with col_user_2:
        if st.button("🔍 Ingresar", use_container_width=True):
            if user_input != st.session_state.user:
                actualizar_url("Cliente", user_input)

    user_clean = st.session_state.user.strip().lower()

    if not user_clean:
        st.info("👆 Ingresa tu ID de usuario arriba para ver tus pedidos.")
    else:
        try:
            user_doc_ref = db.collection("usuarios_perfil").document(user_clean)
            user_doc = user_doc_ref.get()
            
            if not user_doc.exists and user_clean not in [adm.lower() for adm in ADMINS_AUTORIZADOS]:
                st.error("❌ El usuario ingresado no existe o no está registrado en el sistema. Por favor, verifica tu ID.")
            else:
                nombre_cliente = st.session_state.user
                logo_cliente_url = None
                if user_doc.exists:
                    data_u = user_doc.to_dict()
                    nombre_cliente = data_u.get('nombre_usuario', st.session_state.user)
                    logo_cliente_url = data_u.get('logo_url') or data_u.get('logo_b64')

                col_c1, col_c2 = st.columns([0.1, 3.9], vertical_alignment="center")
                with col_c1:
                    if logo_cliente_url:
                        try:
                            st.image(logo_cliente_url, width=85)
                        except Exception:
                            st.markdown("<h1>👤</h1>", unsafe_allow_html=True)
                    else:
                        st.markdown("<h1>👤</h1>", unsafe_allow_html=True)
                with col_c2:
                    st.markdown(f"<h1 style='margin:0; font-size:2.2rem !important;'>Hola, {nombre_cliente}</h1>", unsafe_allow_html=True)

                if st.session_state.mensaje_exito:
                    st.success(st.session_state.mensaje_exito)
                    st.session_state.mensaje_exito = ""

                st.markdown("---")
                fv = st.session_state.form_version

                with st.expander("➕ Enviar Nuevo Pedido", expanded=st.session_state.expandir_nuevo_pedido):
                    tipo_producto = st.radio("Tipo de Producto:", ["GORRA", "TELA", "VARIOS"], horizontal=True, key=f"prod_{fv}")
                    ubicacion, estilo_frente = "N/A", "N/A"

                    if tipo_producto == "GORRA":
                        ubicacion = st.radio("Ubicación:", ["FRENTE", "TRASERO", "LATERAL"], horizontal=True, key=f"ubi_{fv}")
                        if ubicacion == "FRENTE":
                            estilo_frente = st.radio("Estilo:", ["PLANO"], horizontal=True, key=f"est_{fv}")

                    nombre_proyecto = st.text_input("Nombre del Proyecto", key=f"nom_{fv}")
                    archivos_subidos = st.file_uploader("Archivos (Sin límite de 1MB):", type=["png", "jpg", "jpeg", "dst", "pes", "pdf", "emb"], accept_multiple_files=True, key=f"arch_{fv}")
                    comentarios = st.text_area("Comentarios", key=f"com_{fv}")
                    status_ph = st.empty()

                    if st.button("🚀 ENVIAR PEDIDO", key=f"btn_env_{fv}"):
                        if not nombre_proyecto:
                            status_ph.warning("⚠️ Ingresa el nombre del proyecto.")
                        elif not archivos_subidos:
                            status_ph.error("❌ Adjunta al menos un archivo.")
                        else:
                            try:
                                status_ph.info("⏳ Subiendo archivos...")
                                lista_archivos = []
                                timestamp_num = int(datetime.now().timestamp())
                                
                                for arch in archivos_subidos:
                                    nombre_unico = f"{timestamp_num}_{arch.name}"
                                    url_publica = subir_a_cloudinary(arch, nombre_unico)
                                    
                                    if url_publica:
                                        lista_archivos.append({"nombre": arch.name, "url": url_publica})

                                data_pedido = {
                                    "id": f"PT-{timestamp_num}",
                                    "cliente": st.session_state.user.strip(),
                                    "nombre_proyecto": nombre_proyecto,
                                    "producto": tipo_producto,
                                    "ubicacion": ubicacion,
                                    "estilo": estilo_frente,
                                    "archivos": lista_archivos,
                                    "archivos_finales": [],
                                    "comentarios": comentarios,
                                    "estado": "Pendiente",
                                    "turno": 1,
                                    "timestamp": datetime.now()
                                }
                                db.collection("pedidos_bordado").add(data_pedido)
                                recalcular_turnos()

                                st.session_state.mensaje_exito = "🎉 ¡Pedido enviado con éxito!"
                                st.session_state.form_version += 1
                                st.session_state.expandir_nuevo_pedido = False
                                st.rerun()
                            except Exception as e:
                                status_ph.error(f"Error al enviar: {e}")

                st.markdown("---")
                
                # Renderiza las tablas con auto-refresco silencioso
                renderizar_tablas_cliente(user_clean)

        except Exception as e:
            st.error(f"Error: {e}")

# =========================================================
# VISTA ADMINISTRADOR
# =========================================================
else:
    st.subheader("🛠️ Administración General")
    try:
        renderizar_panel_admin()
    except Exception as e:
        st.error(f"Error en panel admin: {e}")
