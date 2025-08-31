import streamlit as st
import math

st.title("Cálculo de Personal Necesario")

# === Entradas ===
cargo = st.text_input("Cargo del personal (ej: Operador de Máquina)", "Operador")
personal_actual = st.number_input("Cantidad de personal actual en el cargo", min_value=1, value=19, step=1)
ausentismo = st.number_input("Porcentaje de ausentismo (%)", min_value=0.0, value=5.0, step=0.1) / 100
dias_semana = st.number_input("Días a cubrir por semana", min_value=1, max_value=7, value=7, step=1)
horas_promedio = st.number_input("Horas promedio semanales por operador (últimas 3 semanas)", min_value=1, value=42, step=1)
vacaciones = st.number_input("Personal de vacaciones en el período de programación", min_value=0, value=0, step=1)
operadores_turno = st.number_input("Cantidad de operadores requeridos por turno", min_value=1, value=6, step=1)
turnos_dia = st.number_input("Cantidad de turnos por día", min_value=1, max_value=3, value=3, step=1)

# === Cálculo de horas requeridas en la operación ===
horas_operacion_semana = operadores_turno * turnos_dia * dias_semana * 8
horas_operacion_periodo = horas_operacion_semana * 3   # periodo de 3 semanas

# === Horas disponibles por operador (teniendo en cuenta ausentismo y vacaciones) ===
eficiencia = 1 - ausentismo
horas_disponibles_por_operador = horas_promedio * 3 * eficiencia

# Personal necesario
personal_necesario = math.ceil(horas_operacion_periodo / horas_disponibles_por_operador)

# Ajuste por vacaciones
personal_necesario += vacaciones

faltante = personal_necesario - personal_actual

# === Layout en dos columnas ===
col1, col2 = st.columns([2,1])

with col1:
    st.subheader("📊 Resultados del cálculo")

    st.markdown(
        f"""
        <div style="font-size:24px; font-weight:bold; margin-bottom:10px;">
            Personal necesario: {personal_necesario}  
            &nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp; 
            <span style="color:red;">Personal faltante: {faltante}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write(f"**Horas a cubrir por semana:** {horas_operacion_semana}")
    st.write(f"**Horas a cubrir en 3 semanas:** {horas_operacion_periodo}")
    st.write(f"**Horas disponibles por operador en 3 semanas (ajustado por ausentismo):** {horas_disponibles_por_operador:.2f}")
    st.write(f"**Personal actual:** {personal_actual}")

with col2:
    st.subheader("📊 Formulas Utilizadas")
st.markdown("### 1. Horas de operación por semana")
st.code("Operadores por turno × Turnos por día × Días por semana × Horas por turno")

st.markdown("### 2. Horas de operación en 3 semanas")
st.code("Horas de operación por semana × 3")

st.markdown("### 3. Horas disponibles por operador en 3 semanas")
st.code("Horas promedio semanales × 3 × (1 - Porcentaje de ausentismo)")

st.markdown("### 4. Número de operadores necesarios")
st.code("Horas de operación en 3 semanas ÷ Horas disponibles por operador en 3 semanas")

#PROGRAMACIÓN DE TURNOS

import streamlit as st
import pandas as pd
import random

# --------------------------
# Configuración inicial
# --------------------------
st.title("📅 Simulador de Programación de Turnos")

# Número de operadores
num_operadores = st.number_input("Ingrese el número de operadores:", min_value=1, value=10)

# Selección de modelo
modelo = st.radio("Seleccione el modelo de programación:", ["Modelo 124 horas", "Modelo 128 horas"])

# --------------------------
# Definición de turnos según modelo
# --------------------------
if modelo == "Modelo 124 horas":
    turnos = ["T1 (8h)", "T2 (8h)", "T3 (8h)"]  # 3 turnos de 8h
    dias_por_semana = 7
elif modelo == "Modelo 128 horas":
    turnos = ["T1 (12h)", "T2 (12h)"]  # 2 turnos de 12h
    dias_por_semana = 7

# --------------------------
# Construcción de la grilla
# --------------------------
# Crear nombres de columnas: "Lunes S1", ..., "Domingo S3"
dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
columnas = ["Operador"] + [f"{dia} S{sem}" for sem in range(1, 4) for dia in dias_semana]

# Crear estructura vacía
programacion = []

for i in range(num_operadores):
    fila = [f"Operador {i+1}"]  # primera columna
    # asignar turnos aleatoriamente garantizando cobertura
    for sem in range(3):  # 3 semanas
        for d in range(dias_por_semana):
            turno_asignado = random.choice(turnos)
            fila.append(turno_asignado)
    programacion.append(fila)

# --------------------------
# Mostrar en tabla
# --------------------------
df = pd.DataFrame(programacion, columns=columnas)
st.dataframe(df, use_container_width=True)

        st.subheader("Programación - Modelo 128 horas")
        st.dataframe(df)
