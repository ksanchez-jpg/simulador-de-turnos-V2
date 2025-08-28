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
import pandas as pd
import random

# -----------------------------
# ENTRADAS DEL USUARIO
# -----------------------------
tipo_turno = int(input("¿Turnos de cuántas horas? (8 o 12): "))
total_operadores = int(input("¿Cuántos operadores en total?: "))
min_operadores_turno = int(input("¿Mínimo de operadores por turno?: "))
semanas = int(input("¿Cuántas semanas quieres programar?: "))

# Definir número de turnos
if tipo_turno == 8:
    num_turnos = 3
elif tipo_turno == 12:
    num_turnos = 2
else:
    raise ValueError("Debes ingresar 8 o 12.")

# Crear lista de operadores
operadores = [f"Op{i+1}" for i in range(total_operadores)]

# Definir días de la semana
dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# Crear la estructura de asignación
asignacion = {turno: {op: [] for op in operadores} for turno in range(1, num_turnos+1)}

# -----------------------------
# PROGRAMACIÓN AUTOMÁTICA
# -----------------------------
for semana in range(1, semanas+1):
    for dia in dias_semana:
        disponibles = operadores.copy()
        random.shuffle(disponibles)  # rotación aleatoria cada día
        
        for turno in range(1, num_turnos+1):
            asignados = disponibles[:min_operadores_turno]   # operadores que trabajan en este turno
            disponibles = disponibles[min_operadores_turno:] # los que sobran siguen disponibles
            
            for op in operadores:
                if op in asignados:
                    asignacion[turno][op].append(f"{tipo_turno}h")
                else:
                    asignacion[turno][op].append("Descanso")

# -----------------------------
# CREAR Y MOSTRAR TABLAS
# -----------------------------
columnas = []
for s in range(1, semanas+1):
    columnas.extend([f"{d} Sem{s}" for d in dias_semana])

for turno in range(1, num_turnos+1):
    data = { "Operador": operadores }
    for idx, op in enumerate(operadores):
        data[op] = asignacion[turno][op]
    df = pd.DataFrame(asignacion[turno]).T
    df["Operador"] = df.index
    df.reset_index(drop=True, inplace=True)
    df.columns = ["Operador"] + columnas
    print(f"\n--- 📋 PROGRAMACIÓN TURNO {turno} ---")
    display(df)

