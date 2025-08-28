import streamlit as st
import pandas as pd
import math

# -------------------- CONFIGURACIÓN APP --------------------
st.set_page_config(
    page_title="CÁLCULO Y PROGRAMACIÓN DE TURNOS",
    page_icon="📋",
    layout="wide"
)

st.title("📋 CÁLCULO DE PERSONAL Y PROGRAMACIÓN DE TURNOS")
st.caption("Generador de programación automática de turnos en tablas separadas.")

# -------------------- ENTRADAS --------------------
col1, col2 = st.columns(2)

with col1:
    cargo = st.text_input("Nombre del cargo", value="Operador")
    ausentismo_pct = st.number_input("% de ausentismo", 0.0, 100.0, 8.0, step=0.5)
    horas_prom_bisem = st.number_input("Horas por semana (promedio bisemanal)", 10.0, 60.0, 42.0, step=0.5)
    personal_vacaciones = st.number_input("Personal de vacaciones", min_value=0, value=0, step=1)

with col2:
    personas_actuales = st.number_input("Total de personas actuales en el cargo", min_value=0, value=6, step=1)
    dias_cubrir = st.number_input("Días a cubrir en la semana", 1, 7, 7, step=1)
    config_turnos = st.selectbox("Configuración de turnos", ("3 turnos de 8 horas", "2 turnos de 12 horas"))
    dias_vacaciones = st.number_input("Días de vacaciones", min_value=0, value=0, step=1)
    min_operadores_turno = st.number_input("Cantidad mínima de operadores por turno", 1, value=3, step=1)

# -------------------- CONFIGURACIÓN DE TURNOS --------------------
if "3 turnos" in config_turnos:
    n_turnos_dia, horas_por_turno = 3, 8
else:
    n_turnos_dia, horas_por_turno = 2, 12

# -------------------- CÁLCULO DE PERSONAL --------------------
horas_semana_requeridas = dias_cubrir * n_turnos_dia * horas_por_turno * min_operadores_turno
factor_disponibilidad = 1.0 - (ausentismo_pct / 100.0)

if factor_disponibilidad <= 0:
    st.error("El % de ausentismo no puede ser 100% o más.")
    st.stop()

horas_semana_ajustadas = horas_semana_requeridas / factor_disponibilidad
personal_requerido_base = horas_semana_ajustadas / horas_prom_bisem

# Ajuste por vacaciones
horas_vacaciones = personal_vacaciones * dias_vacaciones * horas_por_turno
personal_requerido_vacaciones = horas_vacaciones / horas_prom_bisem

# Total requerido
personal_total_requerido = math.ceil(personal_requerido_base + personal_requerido_vacaciones)
brecha = personal_total_requerido - personas_actuales

# -------------------- RESULTADOS --------------------
st.subheader("📊 Resultados")
st.metric("Personal total necesario", f"{personal_total_requerido}")
st.metric("Brecha de personal (faltante)", f"{brecha}")

st.divider()


# -------------------- PROGRAMACIÓN DE TURNOS --------------------
import streamlit as st
import pandas as pd
import random

st.title("📅 Programación Automática de Turnos")

# Entradas del usuario
tipo_turno = st.selectbox("Selecciona duración del turno", ["8H", "12H"])
total_operadores = st.number_input("Número total de operadores", min_value=1, value=12)
min_operadores = st.number_input("Mínimo de operadores por turno", min_value=1, value=3)
num_semanas = st.number_input("Número de semanas a programar", min_value=1, value=2)

# Calcular número de turnos posibles
num_turnos = total_operadores // min_operadores
st.write(f"Se pueden programar **{num_turnos} turnos** con al menos {min_operadores} operadores por turno")

# Crear lista de operadores
operadores = [f"Op{i+1}" for i in range(total_operadores)]

# Dividir operadores en turnos
turnos = [operadores[i::num_turnos] for i in range(num_turnos)]

# Días y semanas
dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
columnas = [f"{d} Sem{s+1}" for s in range(num_semanas) for d in dias]

# Generar las tablas de turnos
for t, grupo in enumerate(turnos, start=1):
    data = []
    for op in grupo:
        fila = []
        for c in columnas:
            # Rotar descanso: probabilidad de descanso menor si hay pocos operadores
            if random.random() < 1/len(grupo):
                fila.append("Descanso")
            else:
                fila.append(tipo_turno)
        data.append([op] + fila)
    
    df = pd.DataFrame(data, columns=["Operador"] + columnas)
    
    st.subheader(f"Turno {t}")
    st.dataframe(df)

