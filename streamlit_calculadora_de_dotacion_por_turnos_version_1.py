import streamlit as st
import math

# Título de la aplicación
st.title("📊 Calculadora de Personal y Programación de Turnos")

st.write("Ingrese los parámetros a continuación para calcular el personal necesario y generar la programación de turnos.")

# Entradas del usuario
operadores_por_turno = st.number_input("Operadores por turno", min_value=1, value=6)
turnos_por_dia = st.number_input("Turnos por día", min_value=1, value=3)
dias_por_semana = st.number_input("Días por semana", min_value=1, max_value=7, value=7)
horas_por_turno = st.number_input("Horas por turno", min_value=1, value=8)
horas_promedio_semanales = st.number_input("Horas promedio semanales por operador", min_value=1, value=42)
porcentaje_ausentismo = st.number_input("Porcentaje de ausentismo (%)", min_value=0.0, max_value=100.0, value=6.0) / 100

# Cálculos
horas_operacion_semana = operadores_por_turno * turnos_por_dia * dias_por_semana * horas_por_turno
horas_operacion_3_semanas = horas_operacion_semana * 3
horas_disponibles_operador = horas_promedio_semanales * 3 * (1 - porcentaje_ausentismo)
numero_operadores_necesarios = math.ceil(horas_operacion_3_semanas / horas_disponibles_operador)

# Resultados paso a paso
st.subheader("📌 Resultados del cálculo")

st.markdown("### 1. Horas de operación por semana")
st.code("Operadores por turno × Turnos por día × Días por semana × Horas por turno")
st.write(f"**Resultado:** {horas_operacion_semana} horas/semana")

st.markdown("### 2. Horas de operación en 3 semanas")
st.code("Horas de operación por semana × 3")
st.write(f"**Resultado:** {horas_operacion_3_semanas} horas")

st.markdown("### 3. Horas disponibles por operador en 3 semanas")
st.code("Horas promedio semanales × 3 × (1 - Porcentaje de ausentismo)")
st.write(f"**Resultado:** {horas_disponibles_operador:.2f} horas por operador")

st.markdown("### 4. Número de operadores necesarios")
st.code("Horas de operación en 3 semanas ÷ Horas disponibles por operador en 3 semanas")
st.write(f"**Resultado:** {numero_operadores_necesarios} operadores")
