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

# --- Función para generar programación ---
def generar_programacion(num_operadores, horas_totales, turno):
    """
    Genera la programación de turnos
    num_operadores: cantidad de operadores
    horas_totales: horas a programar en 3 semanas
    turno: "8H" o "12H"
    """
    dias = 21  # 3 semanas
    operadores = [f"Operador {i+1}" for i in range(num_operadores)]
    programacion = {op: [] for op in operadores}

    # Determinar cuántos turnos equivalen a las horas necesarias
    horas_turno = 8 if turno == "8H" else 12
    turnos_necesarios = horas_totales // horas_turno

    # Distribuir turnos equitativos
    for op in operadores:
        asignados = 0
        for d in range(dias):
            if asignados < turnos_necesarios and random.random() > 0.5:
                programacion[op].append(f"T1 {turno}")
                asignados += 1
            else:
                programacion[op].append("DESC")
        # Si aún no completó los turnos, llenar al final
        while asignados < turnos_necesarios:
            for d in range(dias):
                if programacion[op][d] == "DESC":
                    programacion[op][d] = f"T1 {turno}"
                    asignados += 1
                    if asignados == turnos_necesarios:
                        break

    # Convertir a DataFrame
    df = pd.DataFrame(programacion).T
    df.columns = [f"Día {i+1}" for i in range(dias)]
    return df

# --- Interfaz Streamlit ---
st.title("📅 Programación de Turnos (3 semanas)")
st.write("Genera turnos de 8H o 12H, con horas equilibradas entre operadores.")

# Parámetros de entrada
num_operadores = st.number_input("Número de operadores", min_value=1, value=6)

# Botones para generar programación
col1, col2 = st.columns(2)
with col1:
    if st.button("Generar con 124 horas (3 semanas)"):
        df = generar_programacion(num_operadores, 124, "8H")
        st.subheader("📊 Programación - 124 horas (8H)")
        st.dataframe(df)

with col2:
    if st.button("Generar con 128 horas (3 semanas)"):
        df = generar_programacion(num_operadores, 128, "12H")
        st.subheader("📊 Programación - 128 horas (12H)")
        st.dataframe(df)


