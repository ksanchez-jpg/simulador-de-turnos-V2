import streamlit as st
import pandas as pd
import math

# ===============================
# 1. Cálculo de personal necesario
# ===============================
st.title("📊 Planificación de Personal y Turnos")

# Entradas de usuario
st.sidebar.header("Parámetros de Producción")
produccion_diaria = st.sidebar.number_input("Producción diaria (ton)", min_value=0, value=500)
capacidad_operador = st.sidebar.number_input("Capacidad de corte por operador (ton/día)", min_value=1, value=50)
dias_laborales = st.sidebar.number_input("Días laborales al mes", min_value=1, value=30)

# Cálculo de operadores
operadores_necesarios = math.ceil(produccion_diaria / capacidad_operador)
total_operadores = operadores_necesarios
st.metric("👷‍♂️ Operadores necesarios por día", operadores_necesarios)

# ===============================
# 2. Programación de turnos
# ===============================
st.header("🗓️ Programación de Turnos (4 Semanas)")

# Selección del esquema de turnos
esquema = st.selectbox("Seleccione esquema de turnos", ["3x8h", "2x12h", "4x6h"])
if esquema == "3x8h":
    num_turnos = 3
elif esquema == "2x12h":
    num_turnos = 2
else:
    num_turnos = 4

# Distribución de operadores entre turnos
operadores_por_turno = total_operadores // num_turnos

# Cantidad mínima de operadores por turno
min_operadores_turno = st.number_input(
    "Cantidad mínima de operadores por turno", min_value=1, value=2, step=1
)

# Función para generar programación de un turno
def generar_programacion(operadores, semanas=4, turno_id=1):
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    data = {}
    for semana in range(1, semanas+1):
        for dia in dias:
            data[f"Semana {semana} | {dia}"] = []

    # Programar operadores asegurando mínimo requerido
    for semana in range(1, semanas+1):
        for dia in dias:
            activos = operadores[:min_operadores_turno]  # los que trabajan
            descansan = operadores[min_operadores_turno:]  # el resto descansa

            for op in operadores:
                if op in activos:
                    data[f"Semana {semana} | {dia}"].append(f"Turno {turno_id}")
                else:
                    data[f"Semana {semana} | {dia}"].append("DESCANSA")

            # Rotación simple: mover lista para que no siempre trabajen los mismos
            operadores = operadores[min_operadores_turno:] + operadores[:min_operadores_turno]

    df = pd.DataFrame(data, index=operadores)
    return df

# Crear una tabla para cada turno
for turno in range(1, num_turnos+1):
    st.subheader(f"📋 Programación Turno {turno}")

    # Asignar operadores a este turno
    operadores_turno = [
        f"OP-{i+1 + (turno-1)*operadores_por_turno}" 
        for i in range(operadores_por_turno)
    ]

    df_turno = generar_programacion(operadores_turno, semanas=4, turno_id=turno)
    st.dataframe(df_turno)
