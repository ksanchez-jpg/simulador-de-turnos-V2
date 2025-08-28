import streamlit as st
import pandas as pd
import math

# -------------------- CONFIGURACIÓN DE LA APP --------------------
st.set_page_config(
    page_title="CÁLCULO DE PERSONAL REQUERIDO",
    page_icon="🧮",
    layout="centered"
)

st.title("🧮 CÁLCULO DE PERSONAL REQUERIDO Y PROGRAMACIÓN DE TURNOS")
st.caption("Versión 3 – Cálculo optimizado + programación básica de operadores por turno.")

# -------------------- ENTRADAS --------------------
col1, col2 = st.columns(2)

with col1:
    cargo = st.text_input("Nombre del cargo", value="Operador")
    ausentismo_pct = st.number_input("% de ausentismo", 0.0, 100.0, 8.0, step=0.5)
    horas_prom_bisem = st.number_input("Horas por semana (promedio bisemanal)", 10.0, 60.0, 42.0, step=0.5)
    personal_vacaciones = st.number_input("Personal de vacaciones", min_value=0, value=0, step=1)

with col2:
    personas_actuales = st.number_input("Total de personas actuales en el cargo", min_value=0, value=0, step=1)
    dias_cubrir = st.number_input("Días a cubrir en la semana", 1, 7, 7, step=1)
    config_turnos = st.selectbox(
        "Configuración de turnos",
        ("3 turnos de 8 horas", "2 turnos de 12 horas"),
    )
    dias_vacaciones = st.number_input("Días de vacaciones", min_value=0, value=0, step=1)
    min_operadores_turno = st.number_input("Cantidad mínima de operadores por turno", 1, value=3, step=1)

# -------------------- CONFIGURACIÓN DE TURNOS --------------------
if "3 turnos" in config_turnos:
    n_turnos_dia, horas_por_turno = 3, 8
else:
    n_turnos_dia, horas_por_turno = 2, 12

# -------------------- CÁLCULOS --------------------
# Horas requeridas en la semana
horas_semana_requeridas = dias_cubrir * n_turnos_dia * horas_por_turno * min_operadores_turno

# Ajuste por ausentismo
factor_disponibilidad = 1.0 - (ausentismo_pct / 100.0)
if factor_disponibilidad <= 0:
    st.error("El % de ausentismo no puede ser 100% o más.")
    st.stop()

horas_semana_ajustadas = horas_semana_requeridas / factor_disponibilidad

# Personal base requerido (sin vacaciones)
personal_requerido_base = horas_semana_ajustadas / horas_prom_bisem

# Ajuste por vacaciones (más realista: carga laboral semanal promedio)
horas_dia_promedio = horas_prom_bisem / dias_cubrir
horas_vacaciones = personal_vacaciones * dias_vacaciones * horas_dia_promedio
personal_requerido_vacaciones = horas_vacaciones / horas_prom_bisem

# Total personal requerido
personal_total_requerido = math.ceil(personal_requerido_base + personal_requerido_vacaciones)
brecha = personal_total_requerido - personas_actuales

# -------------------- RESULTADOS --------------------
st.subheader("📊 Resultados del cálculo")

col_res1, col_res2, col_res3 = st.columns(3)
col_res1.metric("Personal requerido (sin vacaciones)", f"{math.ceil(personal_requerido_base)}")
col_res2.metric("Personal adicional por vacaciones", f"{math.ceil(personal_requerido_vacaciones)}")
col_res3.metric("Total personal necesario", f"{personal_total_requerido}")

st.metric("Brecha frente al personal actual", f"{brecha:+}")

# -------------------- PROGRAMACIÓN DE TURNOS --------------------
st.divider()
st.subheader("📅 Programación mínima de turnos (cobertura)")

# Generar tabla con días y turnos
dias = [f"Día {i+1}" for i in range(dias_cubrir)]
turnos = [f"Turno {j+1}" for j in range(n_turnos_dia)]

data = []
for d in dias:
    for t in turnos:
        data.append([d, t, min_operadores_turno])

df_turnos = pd.DataFrame(data, columns=["Día", "Turno", f"{cargo}s requeridos"])

st.dataframe(df_turnos, use_container_width=True)

