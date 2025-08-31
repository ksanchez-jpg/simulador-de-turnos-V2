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

st.title("Programación de Turnos")
st.write("Seleccione el modelo de programación que desea generar:")

# Parámetros generales
operadores = ["Operador " + str(i+1) for i in range(20)]
dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# Función para generar turnos
def generar_programacion(modelo):
    programacion = []

    for semana in range(3):  # 3 semanas
        for dia in dias_semana:
            # Definir turnos según modelo
            if modelo == "124":
                turnos = ["Turno 1 (8H)", "Turno 2 (8H)", "Turno 3 (8H)", "Turno 4 (12H)"]
            elif modelo == "128":
                turnos = ["Turno 1 (12H)", "Turno 2 (12H)"]

            for turno in turnos:
                # Seleccionar operadores de forma balanceada
                asignados = random.sample(operadores, 3)
                for op in asignados:
                    programacion.append({
                        "Semana": semana+1,
                        "Día": dia,
                        "Turno": turno,
                        "Operador": op
                    })

    df = pd.DataFrame(programacion)
    return df

# Botones de selección
col1, col2 = st.columns(2)

with col1:
    if st.button("Modelo 124 horas"):
        df = generar_programacion("124")
        st.subheader("Programación - Modelo 124 horas")
        st.dataframe(df)

with col2:
    if st.button("Modelo 128 horas"):
        df = generar_programacion("128")
        st.subheader("Programación - Modelo 128 horas")
        st.dataframe(df)
