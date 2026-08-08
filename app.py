import streamlit as st

# Ejemplo de función para obtener los clientes registrados con su precio configurado
def obtener_clientes():
    # En tu app, esto se consulta desde tu tabla de Supabase / Base de Datos
    return [
        {"id": 1, "nombre": "Cliente Ejemplo A", "precio_base": 15.00},
        {"id": 2, "nombre": "Cliente Ejemplo B", "precio_base": 20.00},
    ]

st.title("📦 Crear Nueva Orden - Pixel Thread")

# 1. Cargar la lista de clientes desde la gestión de clientes
lista_clientes = obtener_clientes()
opciones_clientes = {c["nombre"]: c for c in lista_clientes}

# 2. Formulario principal sin el expansor manual de precio
with st.form("form_crear_orden", clear_on_submit=True):
    # Selección de cliente
    cliente_seleccionado_nombre = st.selectbox("Seleccionar Cliente", list(opciones_clientes.keys()))
    
    # Obtener el precio predeterminado desde los datos del cliente elegido
    cliente_data = opciones_clientes.get(cliente_seleccionado_nombre)
    precio_logo = cliente_data["precio_base"] if cliente_data else 0.0

    # Campos de la orden
    nombre_logo = st.text_input("Nombre del Logo / Arte")
    archivo = st.file_uploader("Cargar Archivo de Bordado", type=["png", "jpg", "dst", "pes", "emb"])
    comentarios = st.text_area("Instrucciones o Notas")

    # Mostrar de forma informativa el precio asignado por el cliente
    st.info(f"💵 **Precio asignado automáticamente:** ${precio_logo:.2f} USD")

    submit = st.form_submit_button("Guardar Orden")

# 3. Guardar orden en la base de datos
if submit:
    if not nombre_logo or not archivo:
        st.error("Por favor completa los campos requeridos.")
    else:
        # Se envía la orden a Supabase usando el precio derivado del cliente
        payload = {
            "cliente_id": cliente_data["id"],
            "nombre_logo": nombre_logo,
            "precio": precio_logo,  # Precio automático de Gestión de Clientes
            "estado": "Pendiente",
            "notas": comentarios
        }
        
        # guardar_en_supabase(payload)
        st.success(f"Orden '{nombre_logo}' creada exitosamente por ${precio_logo:.2f} USD")
