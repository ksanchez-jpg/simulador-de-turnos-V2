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
# Ejemplo: 6 operadores x 3 turnos x 7 días x 8h = horas totales de operación
horas_operacion_semana = operadores_turno * turnos_dia * dias_semana * 8
horas_operacion_periodo = horas_operacion_semana * 3   # periodo de 3 semanas

# === Horas disponibles por operador (teniendo en cuenta ausentismo y vacaciones) ===
eficiencia = 1 - ausentismo
horas_disponibles_por_operador = horas_promedio * 3 * eficiencia

# Personal necesario
personal_necesario = math.ceil(horas_operacion_periodo / horas_disponibles_por_operador)

# Ajuste por vacaciones
personal_necesario += vacaciones

# === Resultados ===
st.subheader("Resultados del cálculo")
st.write(f"**Horas totales de operación por semana:** {horas_operacion_semana}")
st.write(f"**Horas totales de operación en 3 semanas:** {horas_operacion_periodo}")
st.write(f"**Horas disponibles por operador en 3 semanas (ajustado por ausentismo):** {horas_disponibles_por_operador:.2f}")
st.write(f"**Personal necesario (incluyendo vacaciones):** {personal_necesario}")
st.write(f"**Personal actual:** {personal_actual}")
st.write(f"**Diferencia:** {personal_necesario - personal_actual}")
