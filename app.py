import streamlit as st
from datetime import datetime
import cloudinary
import cloudinary.uploader
from supabase import create_client, Client

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
    """Sube archivos pesados a Cloudinary y devuelve URL pública."""
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

# --- INICIALIZACIÓN DE SUPABASE ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["supabase"]["URL"]
    key = st.secrets["supabase"]["KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- CSS PERSONALIZADO ---
st.markdown("""
<style>
    [data-testid="stHeader"], .stAppToolbar, header {
        display: none !important;
        visibility: hidden !important;
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

# --- FUNCIONES AUXILIARES ---
def recalcular_turnos():
    try:
        res = supabase.table("pedidos_bordado").select("id, estado").order("timestamp").execute()
        docs = res.data or []
        turno_actual = 1
        for p in docs:
            doc_id = p["id"]
            estado = p.get("estado", "Pendiente")
            if estado != "Completado":
                supabase.table("pedidos_bordado").update({"turno": str(turno_actual)}).eq("id", doc_id).execute()
                turno_actual += 1
            else:
                supabase.table("pedidos_bordado").update({"turno": "N/A"}).eq("id", doc_id).execute()
    except Exception as e:
        st.error(f"Error recalculando turnos: {e}")

def limpiar_lista_archivos(raw_data):
    if not isinstance(raw_data, list):
        return []
    return [item for item in raw_data if isinstance(item, dict) and "nombre" in item]

def vaciar_pedidos():
    res = supabase.table("pedidos_bordado").delete().neq("id", 0).execute()
    return len(res.data) if res.data else 0

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
    st.session_state.user = user.strip()
    st.query_params["seccion"] = vista
    st.query_params["user"] = user.strip()
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
            if usuario_actual.lower() in [a.lower() for a in ADMINS_AUTORIZADOS]:
                actualizar_url("Admin", st.session_state.user)
            else:
                st.error("❌ Sin permisos.")

st.markdown("<br>", unsafe_allow_html=True)

# =========================================================
# VISTA CLIENTE
# =========================================================
@st.fragment(run_every=10)
def renderizar_tablas_cliente(user_clean):
    if st.session_state.mensaje_exito:
        st.success(st.session_state.mensaje_exito)
        st.session_state.mensaje_exito = ""

    # --- FORMULARIO NUEVO PEDIDO CON LÓGICA CONDICIONAL ACTUALIZADA ---
    with st.expander("➕ NUEVO PEDIDO / ENVIAR LOGO", expanded=st.session_state.expandir_nuevo_pedido):
        v = st.session_state.form_version
        
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            nombre_proy = st.text_input("Nombre del Proyecto / Logo:", key=f"np_nom_{v}").strip()
            tipo_prod = st.radio(
                "Producto a Bordar:", 
                ["GORRA", "TELA", "VARIOS"], 
                key=f"np_prod_{v}"
            )

        with col_f2:
            ubicacion_val = "N/A"
            estilo_val = "PLANO"

            # 1. Si es GORRA
            if tipo_prod == "GORRA":
                ubicacion_val = st.radio(
                    "Ubicación en Gorra:", 
                    ["FRENTE", "TRASERO", "LATERAL"], 
                    key=f"np_ubi_{v}"
                )
                
                # Estilo SOLO para FRENTE
                if ubicacion_val == "FRENTE":
                    estilo_val = st.radio(
                        "Estilo de Bordado:", 
                        ["PLANO", "3D / PUFFY"], 
                        key=f"np_est_{v}"
                    )
                else:
                    st.info("ℹ️ Para ubicación Trasero/Lateral el estilo se asigna como PLANO.")
            
            # 2. Si es TELA
            elif tipo_prod == "TELA":
                st.info("ℹ️ Para Tela el estilo se asigna automáticamente como PLANO.")
                estilo_val = "PLANO"

            # 3. Si es VARIOS
            else:
                estilo_val = st.radio(
                    "Estilo de Bordado:", 
                    ["PLANO", "3D / PUFFY"], 
                    key=f"np_est_{v}"
                )

        comentarios_val = st.text_area("Comentarios / Indicaciones adicionales:", key=f"np_com_{v}")
        archivos_subidos = st.file_uploader(
            "Adjuntar Archivos (Imágenes, PDF, Bordados, etc):", 
            accept_multiple_files=True, 
            key=f"np_arch_{v}"
        )

        if st.button("🚀 ENVIAR PEDIDO", use_container_width=True, key=f"btn_subir_{v}"):
            if not nombre_proy:
                st.error("⚠️ El nombre del proyecto es obligatorio.")
            elif not user_clean:
                st.error("⚠️ Usuario no identificado en el sistema.")
            else:
                try:
                    lista_archivos_guardar = []
                    if archivos_subidos:
                        ts = int(datetime.now().timestamp())
                        for fa in archivos_subidos:
                            url_u = subir_a_cloudinary(fa, f"{user_clean}_{ts}_{fa.name}")
                            if url_u:
                                lista_archivos_guardar.append({"nombre": fa.name, "url": url_u})

                    nuevo_doc = {
                        "cliente": user_clean,
                        "nombre_proyecto": nombre_proy,
                        "producto": tipo_prod,
                        "ubicacion": ubicacion_val,
                        "estilo": estilo_val,
                        "comentarios": comentarios_val,
                        "estado": "Pendiente",
                        "timestamp": datetime.now().isoformat(),
                        "archivos": lista_archivos_guardar,
                        "archivos_finales": []
                    }

                    supabase.table("pedidos_bordado").insert(nuevo_doc).execute()
                    recalcular_turnos()

                    st.session_state.mensaje_exito = f"✅ ¡Pedido '{nombre_proy}' enviado exitosamente!"
                    st.session_state.expandir_nuevo_pedido = False
                    st.session_state.form_version += 1
                    st.rerun()
                except Exception as err:
                    st.error(f"Error al enviar el pedido: {err}")

    # Consulta solo los pedidos del cliente
    res = supabase.table("pedidos_bordado").select("*").eq("cliente", user_clean).order("timestamp").execute()
    mis_pedidos = res.data or []

    pedidos_activos = [p for p in mis_pedidos if p.get('estado') != "Completado"]
    pedidos_terminados = [p for p in mis_pedidos if p.get('estado') == "Completado"]

    # Pestañas con conteo dinámico de pedidos/logos
    tab_pendientes, tab_completados = st.tabs([
        f"⏳ Pedidos Pendientes ({len(pedidos_activos)})", 
        f"✅ Pedidos Completados ({len(pedidos_terminados)})"
    ])

    with tab_pendientes:
        st.subheader("📋 Pedidos en Proceso")
        
        if pedidos_activos:
            for i in range(0, len(pedidos_activos), 4):
                cols = st.columns(4)
                grupo = pedidos_activos[i:i+4]
                for j, p in enumerate(grupo):
                    doc_id = p["id"]
                    with cols[j]:
                        with st.container(border=True):
                            turno_val = p.get('turno', 'N/A')
                            estado_curr = p.get('estado', 'Pendiente')
                            
                            st.markdown(f"**🔢 Turno en Cola:** `#{turno_val}`")
                            st.markdown(f"**🧵 Proyecto:** {p.get('nombre_proyecto', 'N/A')}")
                            st.markdown(f"**📦 Producto:** {p.get('producto', 'N/A')}")
                            st.markdown(f"**📍 Ubicación:** {p.get('ubicacion', 'N/A')}")
                            st.markdown(f"**🎨 Estilo:** {p.get('estilo', 'N/A')}")
                            render_estado_badge(estado_curr)
                            
                            if p.get('comentarios'):
                                st.caption(f"📝 Nota: {p.get('comentarios')}")

                            archivos = limpiar_lista_archivos(p.get('archivos', []))
                            if archivos:
                                st.markdown("📁 **Archivos Adjuntos:**")
                                for arch_item in archivos:
                                    nombre_a = arch_item.get('nombre', 'archivo')
                                    url_a = arch_item.get('url', '')
                                    if url_a:
                                        if nombre_a.lower().endswith(('png', 'jpg', 'jpeg', 'webp')):
                                            st.image(url_a, width=120, caption=nombre_a)
                                        st.markdown(f"📥 [Descargar {nombre_a}]({url_a})")

                            # --- OPCIONES DE MODIFICAR Y ELIMINAR ---
                            st.markdown("---")
                            if estado_curr == "Pendiente":
                                with st.expander("✏️ Editar Pedido"):
                                    nuevo_nombre = st.text_input("Proyecto:", value=p.get('nombre_proyecto', ''), key=f"edit_nom_{doc_id}")
                                    nuevo_prod = st.radio("Producto:", ["GORRA", "TELA", "VARIOS"], index=["GORRA", "TELA", "VARIOS"].index(p.get('producto', 'GORRA')) if p.get('producto') in ["GORRA", "TELA", "VARIOS"] else 0, key=f"edit_prod_{doc_id}")
                                    
                                    nueva_ubi = "N/A"
                                    nuevo_estilo = "PLANO"
                                    
                                    if nuevo_prod == "GORRA":
                                        nueva_ubi = st.radio("Ubicación:", ["FRENTE", "TRASERO", "LATERAL"], index=["FRENTE", "TRASERO", "LATERAL"].index(p.get('ubicacion', 'FRENTE')) if p.get('ubicacion') in ["FRENTE", "TRASERO", "LATERAL"] else 0, key=f"edit_ubi_{doc_id}")
                                        if nueva_ubi == "FRENTE":
                                            nuevo_estilo = st.radio("Estilo:", ["PLANO", "3D / PUFFY"], index=["PLANO", "3D / PUFFY"].index(p.get('estilo', 'PLANO')) if p.get('estilo') in ["PLANO", "3D / PUFFY"] else 0, key=f"edit_est_{doc_id}")
                                    elif nuevo_prod == "TELA":
                                        nuevo_estilo = "PLANO"
                                    else:
                                        nuevo_estilo = st.radio("Estilo:", ["PLANO", "3D / PUFFY"], index=["PLANO", "3D / PUFFY"].index(p.get('estilo', 'PLANO')) if p.get('estilo') in ["PLANO", "3D / PUFFY"] else 0, key=f"edit_est_{doc_id}")
                                        
                                    nuevos_comentarios = st.text_area("Comentarios:", value=p.get('comentarios', ''), key=f"edit_com_{doc_id}")

                                    # --- GESTIÓN DE ARCHIVOS EXISTENTES ---
                                    archivos_actuales = limpiar_lista_archivos(p.get('archivos', []))
                                    if archivos_actuales:
                                        st.markdown("**📂 Archivos subidos previamente:**")
                                        for idx_a, arch in enumerate(archivos_actuales):
                                            col_a1, col_a2 = st.columns([4, 1])
                                            with col_a1:
                                                st.caption(f"📄 {arch.get('nombre', 'archivo')}")
                                            with col_a2:
                                                if st.button("❌", key=f"cli_del_file_{doc_id}_{idx_a}", help="Eliminar este archivo"):
                                                    archivos_actuales.pop(idx_a)
                                                    supabase.table("pedidos_bordado").update({
                                                        "archivos": archivos_actuales
                                                    }).eq("id", doc_id).execute()
                                                    st.success("Archivo eliminado.")
                                                    st.rerun()

                                    nuevos_archivos = st.file_uploader("Agregar nuevos archivos:", type=["png", "jpg", "jpeg", "dst", "pes", "pdf", "emb"], accept_multiple_files=True, key=f"edit_arch_{doc_id}")

                                    if st.button("💾 Guardar Cambios", key=f"btn_save_{doc_id}", use_container_width=True):
                                        lista_arch = archivos_actuales
                                        if nuevos_archivos:
                                            ts = int(datetime.now().timestamp())
                                            for na in nuevos_archivos:
                                                u_url = subir_a_cloudinary(na, f"edit_{doc_id}_{ts}_{na.name}")
                                                if u_url:
                                                    lista_arch.append({"nombre": na.name, "url": u_url})

                                        supabase.table("pedidos_bordado").update({
                                            "nombre_proyecto": nuevo_nombre,
                                            "producto": nuevo_prod,
                                            "ubicacion": nueva_ubi,
                                            "estilo": nuevo_estilo,
                                            "comentarios": nuevos_comentarios,
                                            "archivos": lista_arch
                                        }).eq("id", doc_id).execute()
                                        st.success("¡Pedido actualizado!")
                                        st.rerun()

                                if st.button("🗑️ Eliminar Pedido Completo", key=f"cli_del_{doc_id}", use_container_width=True):
                                    supabase.table("pedidos_bordado").delete().eq("id", doc_id).execute()
                                    recalcular_turnos()
                                    st.success("Pedido eliminado correctamente.")
                                    st.rerun()
                            else:
                                st.caption("🔒 *El pedido está en proceso o producción y no se puede modificar.*")
        else:
            st.info("No tienes pedidos pendientes activos.")

    with tab_completados:
        st.subheader("🎉 Historial de Pedidos Listos")

        if pedidos_terminados:
            for i in range(0, len(pedidos_terminados), 4):
                cols = st.columns(4)
                grupo = pedidos_terminados[i:i+4]
                for j, p in enumerate(grupo):
                    with cols[j]:
                        with st.container(border=True):
                            st.markdown(f"**🧵 Proyecto:** {p.get('nombre_proyecto', 'N/A')}")
                            st.markdown(f"**📦 Producto:** {p.get('producto', 'N/A')}")
                            st.markdown(f"**📍 Ubicación:** {p.get('ubicacion', 'N/A')}")
                            st.markdown(f"**🎨 Estilo:** {p.get('estilo', 'N/A')}")
                            render_estado_badge("Completado")

                            archivos_finales = limpiar_lista_archivos(p.get('archivos_finales', []))
                            if archivos_finales:
                                st.markdown("✨ **Archivos Entregados para Descarga:**")
                                for idx_f, af in enumerate(archivos_finales):
                                    nom_f = af.get('nombre', f'archivo_{idx_f+1}')
                                    url_f = af.get('url', '')
                                    if url_f:
                                        if nom_f.lower().endswith(('png', 'jpg', 'jpeg', 'webp')):
                                            st.image(url_f, width=120, caption=nom_f)
                                        st.markdown(f"📥 [**Descargar {nom_f}**]({url_f})")
                            else:
                                st.warning("⚠️ Sin archivos cargados aún.")
        else:
            st.info("Aún no tienes pedidos completados.")

# =========================================================
# VISTA ADMINISTRADOR
# =========================================================
@st.fragment(run_every=10)
def renderizar_panel_admin():
    recalcular_turnos()
    res = supabase.table("pedidos_bordado").select("*").order("timestamp").execute()
    docs = res.data or []

    pedidos_activos = [p for p in docs if p.get('estado') != "Completado"]
    pedidos_completados_admin = [p for p in docs if p.get('estado') == "Completado"]

    # Pestañas con conteo dinámico para el Administrador
    tab_admin_pend, tab_admin_comp, tab_admin_clientes = st.tabs([
        f"⏳ Pendientes y En Proceso ({len(pedidos_activos)})", 
        f"✅ Completados / Entregados ({len(pedidos_completados_admin)})", 
        "👥 Gestión de Clientes"
    ])

    with tab_admin_pend:
        if pedidos_activos:
            for i in range(0, len(pedidos_activos), 4):
                cols = st.columns(4)
                grupo = pedidos_activos[i:i+4]
                for j, p in enumerate(grupo):
                    doc_id = p["id"]
                    with cols[j]:
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
                                    supabase.table("pedidos_bordado").update({"estado": "En Proceso"}).eq("id", doc_id).execute()
                                    recalcular_turnos()
                                    st.rerun()
                            else:
                                if st.button("🔄 Pendiente", key=f"btn_pendiente_{doc_id}", use_container_width=True):
                                    supabase.table("pedidos_bordado").update({"estado": "Pendiente"}).eq("id", doc_id).execute()
                                    recalcular_turnos()
                                    st.rerun()

                            archivos_cliente = limpiar_lista_archivos(p.get('archivos', []))
                            if archivos_cliente:
                                st.markdown("📁 **Archivos del Cliente:**")
                                for ac in archivos_cliente:
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
                                                supabase.table("pedidos_bordado").update({"archivos_finales": lista_finales}).eq("id", doc_id).execute()
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
                                            timestamp_num = int(datetime.now().timestamp())
                                            
                                            for idx, af in enumerate(archivos_entregables, start=1):
                                                status_subida.info(f"⏳ Subiendo {af.name}...")
                                                nombre_unico = f"entrega_{doc_id}_{timestamp_num}_{af.name}"
                                                url_publica = subir_a_cloudinary(af, nombre_unico)
                                                
                                                if url_publica:
                                                    lista_finales.append({"nombre": af.name, "url": url_publica})
                                                
                                            supabase.table("pedidos_bordado").update({
                                                "archivos_finales": lista_finales,
                                                "estado": "Completado",
                                                "turno": "N/A"
                                            }).eq("id", doc_id).execute()
                                            
                                            recalcular_turnos()
                                            status_subida.success("¡Pedido marcado como Completado!")
                                            st.rerun()
                                        except Exception as e:
                                            status_subida.error(f"Error al subir: {e}")
                                    else:
                                        st.warning("Adjunta al menos un archivo.")

                            if st.button("🗑️ Eliminar Pedido", key=f"mob_del_{doc_id}", use_container_width=True):
                                supabase.table("pedidos_bordado").delete().eq("id", doc_id).execute()
                                recalcular_turnos()
                                st.rerun()
        else:
            st.info("🎉 No hay pedidos pendientes de revisión.")

    with tab_admin_comp:
        if pedidos_completados_admin:
            for i in range(0, len(pedidos_completados_admin), 4):
                cols = st.columns(4)
                grupo = pedidos_completados_admin[i:i+4]
                for j, p in enumerate(grupo):
                    doc_id = p["id"]
                    with cols[j]:
                        with st.container(border=True):
                            st.markdown(f"**👤 {p.get('cliente')}**")
                            st.markdown(f"**🧵 {p.get('nombre_proyecto', 'N/A')}**")
                            st.markdown(f"**📦 Producto:** {p.get('producto', 'N/A')}")
                            st.markdown(f"**📍 Ubicación:** {p.get('ubicacion', 'N/A')}")
                            st.markdown(f"**🎨 Estilo:** {p.get('estilo', 'N/A')}")
                            render_estado_badge("Completado")
                            
                            if st.button("🔄 Marcar como Pendiente", key=f"btn_regresar_pend_{doc_id}", use_container_width=True):
                                supabase.table("pedidos_bordado").update({"estado": "Pendiente"}).eq("id", doc_id).execute()
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
                                                supabase.table("pedidos_bordado").update({"archivos_finales": lista_finales}).eq("id", doc_id).execute()
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
                                                
                                            supabase.table("pedidos_bordado").update({
                                                "archivos_finales": lista_finales
                                            }).eq("id", doc_id).execute()
                                            status_subida.success("¡Archivos agregados!")
                                            st.rerun()
                                        except Exception as e:
                                            status_subida.error(f"Error al subir: {e}")
                                    else:
                                        st.warning("Selecciona al menos un archivo.")

                            if st.button("🗑️ Eliminar Pedido", key=f"mob_del_comp_{doc_id}", use_container_width=True):
                                supabase.table("pedidos_bordado").delete().eq("id", doc_id).execute()
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
                            
                            supabase.table("usuarios_perfil").upsert({
                                "id": nuevo_id,
                                "nombre_usuario": nuevo_nombre,
                                "logo_url": logo_url
                            }).execute()
                            
                            st.success(f"✅ Cliente '{nuevo_nombre}' ({nuevo_id}) registrado correctamente.")
                            st.rerun()
                        except Exception as err:
                            st.error(f"Error al guardar cliente: {err}")

        with st.expander("⚠️ ELIMINAR PEDIDOS (Conservar Clientes)", expanded=False):
            st.warning("Esta opción eliminará TODOS los pedidos para liberar espacio.")
            confirmacion = st.checkbox("Entiendo que se borrará el historial completo de pedidos.")
            if st.button("🔥 ELIMINAR TODOS LOS PEDIDOS", use_container_width=True):
                if confirmacion:
                    try:
                        cant_pedidos = vaciar_pedidos()
                        st.success(f"✅ Se eliminaron {cant_pedidos} pedidos correctamente.")
                        st.rerun()
                    except Exception as err_vaciar:
                        st.error(f"Error al eliminar pedidos: {err_vaciar}")
                else:
                    st.warning("Debes marcar la casilla de confirmación para proceder.")

        st.markdown("---")

        clientes_res = supabase.table("usuarios_perfil").select("*").execute()
        clientes_docs = clientes_res.data or []
        if clientes_docs:
            for i in range(0, len(clientes_docs), 3):
                cols_c = st.columns(3)
                grupo_c = clientes_docs[i:i+3]
                for j, cdata in enumerate(grupo_c):
                    cid = cdata["id"]
                    cnombre = cdata.get('nombre_usuario', 'Sin Nombre')
                    clogo = cdata.get('logo_url')

                    with cols_c[j]:
                        with st.container(border=True):
                            col_img, col_txt = st.columns([1, 3])
                            with col_img:
                                if clogo:
                                    try:
                                        st.image(clogo, width=50)
                                    except Exception:
                                        st.write("🖼️")
                                else:
                                    st.write("👤")
                            with col_txt:
                                st.markdown(f"**{cnombre}**")
                                st.caption(f"ID: `{cid}`")

# --- CONTROL DE RENDERIZADO PRINCIPAL ---
if st.session_state.modo_vista == "Admin":
    renderizar_panel_admin()
else:
    renderizar_tablas_cliente(st.session_state.user.strip())
