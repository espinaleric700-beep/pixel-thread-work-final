import streamlit as st
from supabase import create_client, Client

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Pixel Thread - Nueva Orden", page_icon="📦", layout="wide")

# --- CONEXIÓN A SUPABASE ---
@st.cache_resource
def init_supabase() -> Client:
    try:
        url = st.secrets["supabase"]["URL"]
        key = st.secrets["supabase"]["KEY"]
        return create_client(url, key)
    except KeyError as e:
        st.error(f"⚠️ Error de configuración: Falta la clave {e} en la sección [supabase] de Secrets.")
        st.stop()

supabase = init_supabase()

# --- OBTENER CLIENTES ---
def obtener_clientes():
    try:
        res = supabase.table("clientes").select("id, nombre, precio_defecto").execute()
        return res.data if res.data else []
    except Exception:
        # Retorna lista vacía si la tabla no existe o falla la consulta
        return []

# --- INTERFAZ PRINCIPAL ---
st.title("📦 Crear Nueva Orden - Pixel Thread")

clientes = obtener_clientes()

with st.form("form_nueva_orden", clear_on_submit=True):
    # Selección o ingreso de cliente
    if clientes:
        mapa_clientes = {c["nombre"]: c for c in clientes}
        cliente_nombre = st.selectbox("Seleccionar Cliente", list(mapa_clientes.keys()))
        cliente_data = mapa_clientes[cliente_nombre]
        precio_asignado = float(cliente_data.get("precio_defecto", 0.0))
        cliente_id = cliente_data["id"]
    else:
        st.warning("⚠️ No se detectó la tabla 'clientes' en Supabase. Puedes ingresar el cliente manualmente:")
        cliente_nombre = st.text_input("Nombre del Cliente")
        precio_asignado = 0.0
        cliente_id = None

    # Campos de la orden
    nombre_logo = st.text_input("Nombre del Logo / Arte")
    archivo = st.file_uploader("Cargar Archivo de Bordado", type=["png", "jpg", "dst", "pes", "emb"])
    notas = st.text_area("Instrucciones o Notas", placeholder="Medidas, tipo de tela, observaciones...")

    # Muestra informativa del precio pre-configurado
    if cliente_id:
        st.info(f"💵 **Precio configurado para este cliente:** ${precio_asignado:.2f} USD")

    submit = st.form_submit_button("Guardar Orden")

# --- PROCESAMIENTO Y GUARDADO ---
if submit:
    if not nombre_logo.strip():
        st.error("Por favor ingresa el nombre del logo.")
    elif not cliente_nombre:
        st.error("Por favor especifica un cliente.")
    else:
        with st.spinner("Guardando orden..."):
            try:
                nueva_orden = {
                    "nombre_logo": nombre_logo,
                    "precio": precio_asignado,
                    "notas": notas,
                    "estado": "Pendiente"
                }
                
                if cliente_id:
                    nueva_orden["cliente_id"] = cliente_id

                supabase.table("ordenes").insert(nueva_orden).execute()
                st.success(f"✅ ¡Orden '{nombre_logo}' guardada con éxito!")
            except Exception as e:
                st.error(f"Error al registrar la orden en la base de datos: {e}")
