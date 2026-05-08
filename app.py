import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import os

# --- CONFIGURACIÓN DE LA PÁGINA ---
# Esto pone el icono en la pestaña del navegador
st.set_page_config(
    page_title="Diegos Trucking", 
    page_icon="logo.png", # <--- Aquí va tu logo para la pestaña
    layout="centered"
)

# --- LOGO EN LA PANTALLA PRINCIPAL ---
# Esto pone tu logo grande arriba del título
if os.path.exists("logo.png"):
    st.image("logo.png", width=200) # Puedes ajustar el tamaño aquí



# Para esta fase de prueba en tu computadora, seguiremos usando tu misma base de datos.
DB_NAME = "Logistica_Diegos_Trucking.db"

# --- FUNCIONES DE BASE DE DATOS ---
def inicializar_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Viajes (
                id_viaje INTEGER PRIMARY KEY AUTOINCREMENT,
                id_unidad INTEGER,
                cliente TEXT,
                monto_flete REAL,
                fecha TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Gastos (
                id_gasto INTEGER PRIMARY KEY AUTOINCREMENT,
                id_viaje INTEGER,
                categoria TEXT,
                monto REAL,
                fecha TEXT,
                descripcion TEXT,
                FOREIGN KEY(id_viaje) REFERENCES Viajes(id_viaje)
            )
        ''')
        conn.commit()

def ejecutar_sql(query, params):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        id_generado = cursor.lastrowid
        conn.commit()
        return id_generado

inicializar_db()

# --- INTERFAZ VISUAL WEB ---
st.title("🚛 Logística Diegos Trucking")
st.markdown("Sistema de Control Operativo y Financiero")

# Creamos las pestañas (Tabs)
tab1, tab2, tab3 = st.tabs(["Registro de Viaje", "Gastos Fijos", "Balance y Reportes"])

# ==========================================
# --- PESTAÑA 1: VIAJES ---
# ==========================================
with tab1:
    st.subheader("Datos del Flete")
    
    # st.form agrupa todos los campos hasta que el usuario presione el botón
    with st.form("form_viajes", clear_on_submit=True):
        uni = st.text_input("ID Unidad (1-4)", value="1")
        cli = st.text_input("Cliente / Destino")
        mon = st.number_input("Monto Cobrado ($)", min_value=0.0, step=100.0)
        fec = st.date_input("Fecha", date.today())
        
        st.markdown("---")
        st.markdown("**Gastos Directos de Operación**")
        col1, col2 = st.columns(2) # Divide en dos columnas para que se vea mejor
        with col1:
            cas = st.number_input("Casetas ($)", min_value=0.0, step=50.0)
        with col2:
            man = st.number_input("Maniobras ($)", min_value=0.0, step=50.0)
            
        submit_viaje = st.form_submit_button("Guardar Ingreso Completo", type="primary")

        if submit_viaje:
            if not cli:
                st.error("Por favor ingresa el cliente o destino.")
            else:
                fecha_str = fec.strftime("%Y-%m-%d")
                sql_viaje = "INSERT INTO Viajes (id_unidad, cliente, monto_flete, fecha) VALUES (?, ?, ?, ?)"
                id_viaje = ejecutar_sql(sql_viaje, (uni, cli, mon, fecha_str))
                
                if id_viaje:
                    if cas > 0:
                        ejecutar_sql("INSERT INTO Gastos (id_viaje, categoria, monto, fecha, descripcion) VALUES (?, ?, ?, ?, ?)", 
                                     (id_viaje, 'CASETAS', cas, fecha_str, f"Casetas viaje {id_viaje}"))
                    if man > 0:
                        ejecutar_sql("INSERT INTO Gastos (id_viaje, categoria, monto, fecha, descripcion) VALUES (?, ?, ?, ?, ?)", 
                                     (id_viaje, 'MANIOBRAS', man, fecha_str, f"Maniobras viaje {id_viaje}"))
                
                st.success(f"¡Viaje de {cli} guardado con éxito!")

# ==========================================
# --- PESTAÑA 2: OTROS GASTOS ---
# ==========================================
with tab2:
    st.subheader("Salidas de Dinero")
    
    with st.form("form_gastos", clear_on_submit=True):
        tipo = st.selectbox("Tipo de Gasto", ["DIESEL", "CHOFER", "NOMINAS", "COMPLEMENTOS", "MANTENIMIENTO", "SEGUROS", "CASA", "PENSION"])
        desc = st.text_input("Descripción (Estación, Nombre, Concepto)")
        pago = st.number_input("Monto Pagado ($)", min_value=0.0, step=100.0)
        fec_gasto = st.date_input("Fecha del Gasto", date.today())
        
        submit_gasto = st.form_submit_button("Registrar Gasto", type="primary")
        
        if submit_gasto:
            if not desc:
                st.error("Por favor agrega una descripción.")
            else:
                fecha_g_str = fec_gasto.strftime("%Y-%m-%d")
                sql = "INSERT INTO Gastos (id_viaje, categoria, monto, fecha, descripcion) VALUES (NULL, ?, ?, ?, ?)"
                ejecutar_sql(sql, (tipo, pago, fecha_g_str, desc))
                st.success(f"Gasto de {tipo} registrado correctamente.")

# ==========================================
# --- PESTAÑA 3: REPORTES ---
# ==========================================
with tab3:
    st.subheader("Filtro de Fechas")
    
    col_ini, col_fin = st.columns(2)
    with col_ini:
        f_ini = st.date_input("Desde:", date(2025, 1, 1))
    with col_fin:
        f_fin = st.date_input("Hasta:", date(2026, 12, 31))
        
    f_ini_str = f_ini.strftime("%Y-%m-%d")
    f_fin_str = f_fin.strftime("%Y-%m-%d")

    # Extraer datos de la base
    with sqlite3.connect(DB_NAME) as conn:
        df_viajes = pd.read_sql_query(f"SELECT id_viaje, fecha, id_unidad, cliente, monto_flete FROM Viajes WHERE fecha BETWEEN '{f_ini_str}' AND '{f_fin_str}'", conn)
        df_gastos = pd.read_sql_query(f"SELECT id_gasto, fecha, categoria, descripcion, monto FROM Gastos WHERE fecha BETWEEN '{f_ini_str}' AND '{f_fin_str}'", conn)

    # Cálculos
    tot_ingresos = df_viajes['monto_flete'].sum() if not df_viajes.empty else 0.0
    tot_gastos = df_gastos['monto'].sum() if not df_gastos.empty else 0.0
    utilidad = tot_ingresos - tot_gastos

    # Mostrar en tarjetas visuales
    st.markdown("### Balance del Periodo")
    m1, m2, m3 = st.columns(3)
    m1.metric("Ingresos Totales", f"${tot_ingresos:,.2f}")
    m2.metric("Gastos Totales", f"${tot_gastos:,.2f}")
    m3.metric("Utilidad Neta", f"${utilidad:,.2f}", delta=float(utilidad))

    st.markdown("---")
    
    # Mostrar las tablas interactivas en la misma web
    st.markdown("#### Detalle de Viajes")
    st.dataframe(df_viajes, use_container_width=True, hide_index=True)
    
    st.markdown("#### Detalle de Gastos")
    st.dataframe(df_gastos, use_container_width=True, hide_index=True)

    # Botón mágico de exportación a CSV integrado
    # Almacenamos el CSV en memoria para descargar directo al navegador
    csv_viajes = df_viajes.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 Descargar Viajes (Excel/CSV)",
        data=csv_viajes,
        file_name='viajes_diego.csv',
        mime='text/csv',
    )
    
    csv_gastos = df_gastos.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 Descargar Gastos (Excel/CSV)",
        data=csv_gastos,
        file_name='gastos_diego.csv',
        mime='text/csv',
    )
# --- SECCIÓN DE RESPALDO (BOTÓN DE DESCARGA) ---
st.sidebar.markdown("---")
st.sidebar.subheader("Seguridad de Datos")

# Leemos el archivo de la base de datos para ofrecerlo como descarga
if os.path.exists(DB_NAME):
    with open(DB_NAME, "rb") as f:
        db_binary = f.read()
    
    st.sidebar.download_button(
        label="📥 Descargar Respaldo (.db)",
        data=db_binary,
        file_name=f"Respaldo_Diegos_{date.today()}.db",
        mime="application/x-sqlite3",
        help="Haz clic aquí para guardar una copia de toda la información en tu dispositivo."
    )