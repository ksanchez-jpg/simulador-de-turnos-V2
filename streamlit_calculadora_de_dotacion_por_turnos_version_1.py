import streamlit as st
import pandas as pd

st.title("Simulador de Turnos")

# Selección del esquema de turnos
opcion_turnos = st.radio(
    "Seleccione el esquema de turnos:",
    ["3 turnos de 8h", "2 turnos de 12h", "4 turnos de 6h"]
)

# Definición de turnos según opción
if opcion_turnos == "3 turnos de 8h":
    turnos = ["Turno 1 (06:00 - 14:00)", "Turno 2 (14:00 - 22:00)", "Turno 3 (22:00 - 06:00)"]
elif opcion_turnos == "2 turnos de 12h":
    turnos = ["Turno 1 (06:00 - 18:00)", "Turno 2 (18:00 - 06:00)"]
elif opcion_turnos == "4 turnos de 6h":
    turnos = [
        "Turno 1 (06:00 - 12:00)",
        "Turno 2 (12:00 - 18:00)",
        "Turno 3 (18:00 - 00:00)",
        "Turno 4 (00:00 - 06:00)"
    ]
else:
    turnos = []

# Generación de tabla de ejemplo con 7 días
dias = [f"Día {i+1}" for i in range(7)]
data = {}

for i, turno in enumerate(turnos, start=1):
    data[turno] = [f"Operador {i}"] * 7

df = pd.DataFrame(data, index=dias)

st.subheader("Programación de turnos (ejemplo)")
st.dataframe(df)
