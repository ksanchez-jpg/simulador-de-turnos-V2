import streamlit as st
import math

st.title("📊 Cálculo de personal requerido")

# Parámetros de entrada
cargo = st.text_input("Nombre del cargo", "Operador")
personas_actuales = st.number_input("Personas en el cargo actualmente", 0, 100, 10)
personas_turno = st.number_input("Personas requeridas por turno", 1, 50, 4)
turnos_dia = st.number_input("Número de turnos por día", 1, 4, 3)
ausentismo = st.number_input("Porcentaje de ausentismo (%)", 0.0, 100.0, 5.0)
personas_vacaciones = st.number_input("Personas en vacaciones simultáneamente", 0, 50, 1)
dias_vacaciones = st.number_input("Días de vacaciones por persona al año", 0, 60, 15)

# Cálculos
dotacion_minima = personas_turno * turnos_dia
dotacion_ausentismo = dotacion_minima / (1 - ausentismo/100)

# Ajuste por vacaciones (aprox)
ajuste_vacaciones = (personas_vacaciones * dias_vacaciones) / 365
dotacion_final = math.ceil(dotacion_ausentismo + ajuste_vacaciones)

# Resultados
st.subheader("📌 Resultados")
st.write(f"🔹 Cargo: **{cargo}**")
st.write(f"🔹 Dotación mínima diaria (sin ajustes): {dotacion_minima} personas")
st.write(f"🔹 Ajuste por ausentismo: {dotacion_ausentismo:.2f}")
st.write(f"🔹 Ajuste por vacaciones: {ajuste_vacaciones:.2f} personas")
st.write(f"✅ **Dotación requerida total: {dotacion_final} personas**")
st.write(f"👥 Actualmente tienes: {personas_actuales} personas")
st.write(f"➡️ Te faltan **{max(0, dotacion_final - personas_actuales)} personas** para cubrir la operación")
