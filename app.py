import streamlit as st
from supabase import create_client, Client

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Pixel Thread - Nueva Orden", page_icon="📦", layout="wide")

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_supabase() -> Client:
    try:
        # Lectura correcta respetando la sección [supabase] del archivo TOML
        url = st.secrets["supabase"]["URL"]
        key = st.secrets["supabase"]["KEY"]
        return create_client(url, key)
    except KeyError as e:
        st.error(f"Error de lectura en Secrets: No se encontró la clave {e} dentro de [supabase].")
        st.stop()

supabase = init_supabase()

# --- OBTENER CLIENTES Y PRECIOS ---
@st.cache_data(ttl=60)
def obtener_clientes():
    try:
        res = supabase.table("clientes").select("id, nombre, precio_defecto").execute()
        return res.data if res.data else []
    except Exception as e:
        st.error(f"Error al conectar con la tabla 'clientes': {e}")
        return []

# --- INTERFAZ PRINCIPAL ---
st.title("📦 Crear Nueva Orden - Pixel Thread")

clientes = obtener_clientes()

if not clientes:
    st.warning("No hay clientes registrados en la base de datos. Agrégalos en el módulo de Gestión de Clientes.")
else:
    mapa_clientes = {c["nombre"]: c for c in clientes}

    with st.form("form_nueva_orden", clear_on_submit=True):
        # Seleccionar el cliente
        cliente_nombre = st.selectbox("Seleccionar Cliente", list(mapa_clientes.keys()))
        cliente_data = mapa_clientes[cliente_nombre]

        # Obtener automáticamente el precio pre-establecido desde Gestión de Clientes
        precio_asignado = float(cliente_data.get("precio_defecto", 0.0))

        # Campos de la orden
        nombre_logo = st.text_input("Nombre del Logo / Arte")
        archivo = st.file_uploader("Cargar Archivo de Bordado", type=["png", "jpg", "dst", "pes", "emb"])
        notas = st.text_area("Instrucciones o Notas", placeholder="Medidas, tipo de tela, observaciones...")

        # Muestra informativa del precio fijado sin campo editable ni expander
        st.info(f"💵 **Precio asignado automáticamente:** ${precio_asignado:.2f} USD")

        submit = st.form_submit_button("Guardar Orden")

    # --- GUARDAR EN BASE DE DATOS ---
    if submit:
        if not nombre_logo.strip():
            st.error("Por favor ingresa el nombre del logo.")
        else:
            with st.spinner("Guardando orden..."):
                try:
                    nueva_orden = {
                        "cliente_id": cliente_data["id"],
                        "nombre_logo": nombre_logo,
                        "precio": precio_asignado,  # Se asigna el valor de Gestión de Clientes
                        "notas": notas,
                        "estado": "Pendiente"
                    }
                    
                    supabase.table("ordenes").insert(nueva_orden).execute()
                    st.success(f"✅ ¡Orden '{nombre_logo}' guardada con éxito por ${precio_asignado:.2f} USD!")
                except Exception as e:
                    st.error(f"Error al registrar la orden en Supabase: {e}")
