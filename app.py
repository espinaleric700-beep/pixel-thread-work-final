import streamlit as st
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import cloudinary
import cloudinary.uploader

# ==========================================
# 1. CONFIGURACIÓN DE CLOUDINARY
# ==========================================
cloudinary.config(
    cloud_name = "oik5ivju",
    api_key = "535459971576711",
    api_secret = "J8iAbx6U3AV1_uQJiX3CwCeSR8A",
    secure = True
)

def subir_a_cloudinary(file_obj, nombre_archivo):
    """
    Sube archivos de cualquier tamaño a Cloudinary.
    Soporta imágenes (.png, .jpg) y archivos binarios de bordado (.emb, .dst, .pes, etc.).
    """
    try:
        extension = nombre_archivo.split('.')[-1].lower()
        # "raw" es necesario para extensiones que no son imágenes estándar
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

# ==========================================
# 2. INICIALIZACIÓN DE FIREBASE FIRESTORE
# ==========================================
# (Asegúrate de tener inicializada tu app de Firebase Firestore como habitualmente)
# db = firestore.client()

# ==========================================
# 3. LÓGICA DE ENVÍO DE PEDIDOS (CLIENTE)
# ==========================================
# Inicializar variables en session_state si no existen
if "form_version" not in st.session_state:
    st.session_state.form_version = 1
if "user" not in st.session_state:
    st.session_state.user = "Cliente Demo"

fv = st.session_state.form_version
status_ph = st.empty()

# Campos del formulario
nombre_proyecto = st.text_input("Nombre del Proyecto", key=f"nom_proj_{fv}")
tipo_producto = st.selectbox("Tipo de Producto", ["Gorra", "Camiseta", "Chaqueta", "Otro"], key=f"prod_{fv}")
ubicacion = st.text_input("Ubicación del Bordado", key=f"ubic_{fv}")
estilo_frente = st.text_input("Estilo Frente", key=f"estilo_{fv}")
comentarios = st.text_area("Comentarios o instrucciones", key=f"coment_{fv}")

archivos_subidos = st.file_uploader(
    "Adjunta tus archivos (Imágenes o archivos de bordado .emb, .dst, etc.):",
    accept_multiple_files=True,
    key=f"file_upl_{fv}"
)

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
            
            # Subida de cada archivo adjunto a Cloudinary
            for arch in archivos_subidos:
                nombre_unico = f"{timestamp_num}_{arch.name}"
                url_publica = subir_a_cloudinary(arch, nombre_unico)
                
                if url_publica:
                    lista_archivos.append({
                        "nombre": arch.name,
                        "url": url_publica
                    })

            # Datos a almacenar en Firestore
            data_pedido = {
                "id": f"PT-{timestamp_num}",
                "cliente": st.session_state.user.strip(),
                "nombre_proyecto": nombre_proyecto,
                "producto": tipo_producto,
                "ubicacion": ubicacion,
                "estilo": estilo_frente,
                "archivos": lista_archivos,  # Almacena únicamente las URLs devueltas por Cloudinary
                "archivos_finales": [],
                "comentarios": comentarios,
                "estado": "Pendiente",
                "turno": 1,
                "timestamp": datetime.now()
            }
            
            # Guardar en la colección de Firestore
            db.collection("pedidos_bordado").add(data_pedido)

            st.success("🎉 ¡Pedido enviado con éxito!")
            st.session_state.form_version += 1
            st.rerun()
        except Exception as e:
            status_ph.error(f"Error al enviar el pedido: {e}")
