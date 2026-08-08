import os
import streamlit as st
from supabase import create_client, Client
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

# --- 1. CONFIGURACIÓN E INICIALIZACIÓN ---
st.set_page_config(page_title="Pixel Thread - Nueva Orden", page_icon="📦", layout="wide")

# Conexión a Supabase mediante Secrets de Streamlit
SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.environ.get("SUPABASE_URL"))
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", os.environ.get("SUPABASE_KEY"))

@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# Conexión a Google Drive mediante Service Account
@st.cache_resource
def init_google_drive():
    creds_dict = st.secrets["gcp_service_account"]
    creds = service_account.Credentials.from_service_account_info(
        creds_dict, scopes=['https://www.googleapis.com/auth/drive.file']
    )
    return build('drive', 'v3', credentials=creds)

# --- 2. FUNCIONES AUXILIARES ---
def obtener_clientes_db():
    """Obtiene clientes y su precio por defecto desde Supabase"""
    res = supabase.table("clientes").select("id, nombre, precio_defecto").execute()
    return res.data if res.data else []

def subir_a_drive(file_obj, filename, folder_id):
    """Suba el archivo adjunto a Google Drive y retorna el ID o enlace"""
    drive_service = init_google_drive()
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    media = MediaIoBaseUpload(io.BytesIO(file_obj.getvalue()), mimetype=file_obj.type, resumable=True)
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
    return file.get('webViewLink', '')

# --- 3. INTERFAZ DE USUARIO ---
st.title("📦 Crear Nueva Orden - Pixel Thread")

# Cargar clientes reales
clientes = obtener_clientes_db()

if not clientes:
    st.warning("No se encontraron clientes registrados en el módulo Gestión de Clientes.")
else:
    # Mapear nombres de clientes para el selectbox
    mapa_clientes = {f"{c['nombre']}": c for c in clientes}
    
    with st.form("form_crear_orden", clear_on_submit=True):
        # Selección de cliente
        cliente_nombre = st.selectbox("Seleccionar Cliente", list(mapa_clientes.keys()))
        cliente_info = mapa_clientes[cliente_nombre]
        
        # El precio se obtiene directamente del perfil del cliente seleccionado
        precio_asignado = float(cliente_info.get("precio_defecto", 0.0))

        # Campos de detalle del bordado
        nombre_logo = st.text_input("Nombre del Logo / Arte")
        archivo_adjunto = st.file_uploader(
            "Cargar Archivo de Bordado", 
            type=["png", "jpg", "dst", "pes", "emb"]
        )
        instrucciones = st.text_area("Instrucciones o Notas", placeholder="Medidas, tipo de tela, observaciones...")

        # Muestra informativa del precio pre-establecido en Gestión de Clientes
        st.info(f"💵 **Precio configurado para este cliente:** ${precio_asignado:.2f} USD")

        btn_guardar = st.form_submit_button("Guardar Orden")

    # --- 4. PROCESAMIENTO DE ENVÍO ---
    if btn_guardar:
        if not nombre_logo.strip():
            st.error("Por favor ingresa el nombre del logo o arte.")
        elif not archivo_adjunto:
            st.error("Es necesario adjuntar el archivo de bordado.")
        else:
            with st.spinner("Subiendo archivo a Google Drive y registrando orden..."):
                try:
                    # 1. Subir a Google Drive (ID de carpeta configurado en secrets)
                    folder_id = st.secrets.get("DRIVE_FOLDER_ID", "")
                    drive_url = subir_a_drive(archivo_adjunto, archivo_adjunto.name, folder_id)

                    # 2. Insertar en Supabase
                    datos_orden = {
                        "cliente_id": cliente_info["id"],
                        "nombre_logo": nombre_logo,
                        "precio": precio_asignado,  # Asignado según cliente
                        "archivo_url": drive_url,
                        "notas": instrucciones,
                        "estado": "Pendiente"
                    }
                    
                    supabase.table("ordenes").insert(datos_orden).execute()
                    
                    st.success(f"✅ ¡Orden '{nombre_logo}' registrada correctamente! (Precio: ${precio_asignado:.2f} USD)")
                
                except Exception as e:
                    st.error(f"Error al procesar la orden: {str(e)}")
