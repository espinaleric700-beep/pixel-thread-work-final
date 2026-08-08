import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import cloudinary
import cloudinary.uploader
from PIL import Image
import json

# --- 1. CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Enviar Logo a Pixel Thread",
    page_icon="🧵",
    layout="centered"
)

# --- 2. INICIALIZACIÓN DE FIREBASE ---
@st.cache_resource
def init_firebase():
    if not firebase_admin._apps:
        # Cargar credenciales desde st.secrets ["firebase"]
        firebase_dict = dict(st.secrets["firebase"])
        cred = credentials.Certificate(firebase_dict)
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firebase()

# --- 3. INICIALIZACIÓN DE CLOUDINARY ---
@st.cache_resource
def init_cloudinary():
    cloudinary.config(
        cloud_name=st.secrets["cloudinary"]["cloud_name"],
        api_key=st.secrets["cloudinary"]["api_key"],
        api_secret=st.secrets["cloudinary"]["api_secret"],
        secure=True
    )

init_cloudinary()

# --- 4. FUNCIONES AUXILIARES ---
def obtener_clientes():
    """Obtiene la lista de clientes registrados en Firebase"""
    try:
        docs = db.collection("clientes").stream()
        clientes = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            clientes.append(data)
        return clientes
    except Exception as e:
        st.error(f"Error al obtener clientes de Firebase: {e}")
        return []

# --- 5. INTERFAZ PRINCIPAL ---
st.title("🧵 Enviar Logo a Pixel Thread")

clientes_list = obtener_clientes()

if not clientes_list:
    st.warning("No hay clientes registrados en el sistema. Agrégalos desde la sección de Gestión de Clientes.")
else:
    # Mapeo de clientes
    mapa_clientes = {c.get("nombre", f"Cliente {c['id']}"): c for c in clientes_list}

    with st.form("form_enviar_logo", clear_on_submit=True):
        # Selección de cliente
        cliente_nombre = st.selectbox("Seleccionar Cliente", list(mapa_clientes.keys()))
        cliente_data = mapa_clientes[cliente_nombre]

        # Precio establecido automáticamente desde Gestión de Clientes
        precio_asignado = float(cliente_data.get("precio_defecto", 0.0))

        # Campos de la orden
        nombre_logo = st.text_input("Nombre del Logo / Arte")
        archivo = st.file_uploader(
            "Cargar Archivo de Bordado", 
            type=["png", "jpg", "jpeg", "dst", "pes", "emb"]
        )
        notas = st.text_area("Instrucciones o Notas adicionales")

        # Mostrar el precio asignado sin expander editable
        st.info(f"💵 **Precio configurado para este cliente:** ${precio_asignado:.2f} USD")

        submit = st.form_submit_button("Guardar Orden")

    # --- 6. PROCESAMIENTO Y ENVÍO ---
    if submit:
        if not nombre_logo.strip():
            st.error("Por favor ingresa el nombre del logo.")
        elif not archivo:
            st.error("Por favor adjunta el archivo del logo o bordado.")
        else:
            with st.spinner("Subiendo archivo y creando la orden..."):
                try:
                    # Subir archivo a Cloudinary
                    upload_result = cloudinary.uploader.upload(
                        archivo,
                        resource_type="auto",
                        folder="pixel_thread_logos"
                    )
                    archivo_url = upload_result.get("secure_url")

                    # Estructura de la orden en Firestore
                    nueva_orden = {
                        "cliente_id": cliente_data["id"],
                        "cliente_nombre": cliente_nombre,
                        "nombre_logo": nombre_logo,
                        "precio": precio_asignado,
                        "archivo_url": archivo_url,
                        "notas": notas,
                        "estado": "Pendiente",
                        "creado_en": firestore.SERVER_TIMESTAMP
                    }

                    # Guardar en la colección 'ordenes'
                    db.collection("ordenes").add(nueva_orden)

                    st.success(f"✅ ¡Orden '{nombre_logo}' enviada exitosamente por ${precio_asignado:.2f} USD!")

                except Exception as e:
                    st.error(f"Error al procesar la orden: {e}")
