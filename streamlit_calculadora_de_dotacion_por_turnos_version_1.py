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
import math

st.title("📅 Programación de Turnos - Modelo A y Modelo B")

# Entradas del usuario
num_operadores = st.number_input("Ingrese el número total de operadores disponibles:", min_value=1, value=12)
horas_turno = st.selectbox("Seleccione la duración del turno:", [8, 12])
operadores_por_turno = st.number_input("Ingrese el número de operadores por turno:", min_value=1, value=4)

# Definimos número de turnos por día según duración del turno
if horas_turno == 8:
    turnos_por_dia = 3
else:
    turnos_por_dia = 2

st.write(f"👉 Con turnos de **{horas_turno} horas**, hay **{turnos_por_dia} turnos por día**.")

# Modelos de horas totales
MODELOS = {
    "A": 124,  # en 3 semanas
    "B": 128   # en 3 semanas
}

# Generar programación
def generar_programacion(modelo, horas_totales):
    dias = 21  # 3 semanas
    programacion = []
    
    # Calcular cuántos turnos necesita cada operador
    turnos_por_operador = horas_totales / horas_turno
    
    st.write(f"📌 **Modelo {modelo}**: Cada operador debe trabajar {horas_totales} horas en 3 semanas → {turnos_por_operador:.2f} turnos.")
    
    turno_id = 0
    for dia in range(1, dias+1):
        for turno in range(1, turnos_por_dia+1):
            for op in range(operadores_por_turno):
                operador_asignado = (turno_id % num_operadores) + 1
                programacion.append([f"Día {dia}", f"Turno {turno}", f"Operador {operador_asignado}"])
                turno_id += 1
    
    df = pd.DataFrame(programacion, columns=["Día", "Turno", "Operador"])
    return df

# Mostrar resultados
for modelo, horas in MODELOS.items():
    st.subheader(f"📊 Programación Modelo {modelo}")
    df_programacion = generar_programacion(modelo, horas)
    st.dataframe(df_programacion)
st.subheader("📊 Programación - 128 horas (12H)")
st.dataframe(df)


