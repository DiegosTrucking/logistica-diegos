import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import os

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Diegos Trucking", 
    page_icon="logo.png", 
    layout="centered"
)

# --- LOGO EN LA PANTALLA PRINCIPAL ---
if os.path.exists("logo.png"):
    st.image("logo.png", width=200)

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

tab1, tab2, tab3 = st.tabs(["Registro de Viaje", "Gastos Fijos/Otros", "Balance y Reportes"])

# ==========================================
# --- PESTAÑA 1: VIAJES (AHORA CON DIESEL) ---
# ==========================================
with tab1:
    st.subheader("Datos del Flete")
    
    with st.form("form_viajes", clear_on_submit=True):
        uni = st.selectbox("Unidad", ["1", "2", "3", "4"])
        cli = st.text_input("Cliente / Destino")
        mon = st.number_input("Monto Cobrado ($)", min_value=0.0, step=100.0)
        fec = st.date_input("Fecha", date.today())
        
        st.markdown("---")
        st.markdown("**Gastos Directos del Viaje**")
        col1, col2, col3 = st.columns(3) 
        with col1:
            die = st.number_input("Diesel ($)", min_value=0.0, step=100.0)
        with col2:
            cas = st.number_input("Casetas ($)", min_value=0.0, step=50.0)
        with col3:
            man = st.number_input("Maniobras ($)", min_value=0.0, step=50.0)
            
        submit_viaje = st.form_submit_button("Guardar Viaje y Gastos", type="primary")

        if submit_viaje:
            if not cli:
                st.error("Por favor ingresa el cliente o destino.")
            else:
                fecha_str = fec.strftime("%Y-%m-%d")
                sql_viaje = "INSERT INTO Viajes (id_unidad, cliente, monto_flete, fecha) VALUES (?, ?, ?, ?)"
                id_viaje = ejecutar_sql(sql_viaje, (uni, cli, mon, fecha_str))
                
                if id_viaje:
                    # Registro de los 3 gastos principales del viaje
                    gastos_directos = [
                        ('DIESEL', die),
                        ('CASETAS', cas),
                        ('MANIOBRAS', man)
                    ]
                    for cat, monto in gastos_directos:
                        if monto > 0:
                            ejecutar_sql("INSERT INTO Gastos (id_viaje, categoria, monto, fecha, descripcion) VALUES (?, ?, ?, ?, ?)", 
                                         (id_viaje, cat, monto, fecha_str, f"{cat.capitalize()} viaje {id_viaje} - {cli}"))
                
                st.success(f"¡Viaje y gastos de {cli} registrados con éxito!")

# ==========================================
# --- PESTAÑA 2: OTROS GASTOS (SIN DIESEL) ---
# ==========================================
with tab2:
    st.subheader("Salidas de Dinero (Gastos Generales)")
    
    with st.form("form_gastos", clear_on_submit=True):
        # Se eliminó DIESEL de esta lista
        tipo = st.selectbox("Tipo de Gasto", ["CHOFER", "NOMINAS", "COMPLEMENTOS", "MANTENIMIENTO", "SEGUROS", "CASA", "PENSION", "OTROS"])
        desc = st.text_input("Descripción (Nombre, Concepto, etc.)")
        pago = st.number_input("Monto Pagado ($)", min_value=0.0, step=100.0)
        fec_gasto = st.date_input("Fecha del Gasto", date.today())
        
        submit_gasto = st.form_submit_button("Registrar Gasto General", type="primary")
        
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
        f_ini = st.date_input("Desde:", date(2026, 1, 1))
    with col_fin:
        f_fin = st.date_input("Hasta:", date(2026, 12, 31))
        
    f_ini_str = f_ini.strftime("%Y-%m-%d")
    f_fin_str = f_fin.strftime("%Y-%m-%d")

    with sqlite3.connect(DB_NAME) as conn:
        df_viajes = pd.read_sql_query(f"SELECT id_viaje, fecha, id_unidad, cliente, monto_flete FROM Viajes WHERE fecha BETWEEN '{f_ini_str}' AND '{f_fin_str}'", conn)
        df_gastos = pd.read_sql_query(f"SELECT id_gasto, id_viaje, fecha, categoria, descripcion, monto FROM Gastos WHERE fecha BETWEEN '{f_ini_str}' AND '{f_fin_str}'", conn)

    tot_ingresos = df_viajes['monto_flete'].sum() if not df_viajes.empty else 0.0
    tot_gastos = df_gastos['monto'].sum() if not df_gastos.empty else 0.0
    utilidad = tot_ingresos - tot_gastos

    st.markdown("### Balance del Periodo")
    m1, m2, m3 = st.columns(3)
    m1.metric("Ingresos Totales", f"${tot_ingresos:,.2f}")
    m2.metric("Gastos Totales", f"${tot_gastos:,.2f}")
    m3.metric("Utilidad Neta", f"${utilidad:,.2f}", delta=float(utilidad))

    st.markdown("---")
    st.markdown("#### Detalle de Viajes")
    st.dataframe(df_viajes, use_container_width=True, hide_index=True)
    
    st.markdown("#### Detalle de Gastos")
    st.dataframe(df_gastos, use_container_width=True, hide_index=True)

    csv_viajes = df_viajes.to_csv(index=False).encode('utf-8-sig')
    st.download_button(label="📥 Descargar Viajes", data=csv_viajes, file_name='viajes_diego.csv', mime='text/csv')
    
    csv_gastos = df_gastos.to_csv(index=False).encode('utf-8-sig')
    st.download_button(label="📥 Descargar Gastos", data=csv_gastos, file_name='gastos_diego.csv', mime='text/csv')

# --- BARRA LATERAL ---
st.sidebar.subheader("🚛 Directorio de Flota")
data_unidades = {"Unidad": ["1", "2", "3", "4"], "Placas": ["90BM4W", "93BM4W", "92BM4W", "91BM4W"]}
st.sidebar.table(pd.DataFrame(data_unidades))

st.sidebar.markdown("---")
if os.path.exists(DB_NAME):
    with open(DB_NAME, "rb") as f:
        st.sidebar.download_button(
            label="📥 Descargar Respaldo DB",
            data=f.read(),
            file_name=f"Respaldo_Diegos_{date.today()}.db",
            mime="application/x-sqlite3"
        )