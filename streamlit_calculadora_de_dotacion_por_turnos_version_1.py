import streamlit as st
import pandas as pd
import math
import json
import itertools

st.set_page_config(
    page_title="CÁLCULO DE PERSONAL REQUERIDO Y PROGRAMACIÓN DE TURNOS",
    page_icon="🧮",
    layout="centered"
)

st.title("🧮 CÁLCULO DE PERSONAL REQUERIDO Y PROGRAMACIÓN DE TURNOS")
st.caption("Versión 2 – Incluye cálculo mínimo de personal y programación de turnos con rotación equitativa.")

# ---- Sidebar ----
with st.sidebar:
    st.header("¿Cómo funciona?")
    st.write(
        """
        1. Ingresas parámetros operativos.  
        2. La app estima el **número mínimo de personas necesarias** ajustado por ausentismo y vacaciones.  
        3. Con ese número se genera una **programación de turnos** con rotación equitativa y descansos.
        """
    )

# ---- Entradas ----
col1, col2 = st.columns(2)
with col1:
    cargo = st.text_input("Nombre del cargo", value="Operador")
    ausentismo_pct = st.number_input("% de ausentismo", 0.0, 100.0, 8.0, step=0.5)
    horas_prom_trisem = st.number_input("Horas por semana (promedio trisemanal)", 10.0, 60.0, 42.0, step=0.5)
    personal_vacaciones = st.number_input("Personal de vacaciones", min_value=0, value=0, step=1)

with col2:
    personas_actuales = st.number_input("Total de personas actuales en el cargo", min_value=0, value=0, step=1)
    dias_cubrir = st.number_input("Días a cubrir en la semana", 1, 7, 7, step=1)
    config_turnos = st.selectbox(
        "Configuración de turnos",
        ("3 turnos de 8 horas", "2 turnos de 12 horas"),
    )
    dias_vacaciones = st.number_input("Días de vacaciones", min_value=0, value=0, step=1)

min_operadores_turno = st.number_input("Cantidad mínima de operadores por turno", 1, value=6, step=1)

# ---- Configuración de turnos ----
if "3 turnos" in config_turnos:
    n_turnos_dia, horas_por_turno = 3, 8
elif "2 turnos" in config_turnos:
    n_turnos_dia, horas_por_turno = 2, 12

# ---- Cálculos de personal ----
horas_semana_requeridas = dias_cubrir * n_turnos_dia * horas_por_turno * min_operadores_turno
factor_disponibilidad = 1.0 - (ausentismo_pct / 100.0)
horas_semana_ajustadas = horas_semana_requeridas / factor_disponibilidad

# Personal base requerido
personal_requerido_base = horas_semana_ajustadas / horas_prom_trisem

# Ajuste por vacaciones
horas_vacaciones = personal_vacaciones * dias_vacaciones * 8
personal_requerido_vacaciones = horas_vacaciones / horas_prom_trisem

# Total personal requerido
personal_total_requerido = math.ceil(personal_requerido_base + personal_requerido_vacaciones)
brecha = personal_total_requerido - personas_actuales

# ---- Resultados ----
st.subheader("📊 Resultados del cálculo de personal")
met1, met2, met3 = st.columns(3)
met1.metric("Horas/semana a cubrir", f"{horas_semana_requeridas:,.0f}")
met2.metric("Personal adicional requerido (ajustado)", f"{personal_requerido_base + personal_requerido_vacaciones:,.2f}")
met3.metric("Personal total necesario (redondeo)", f"{personal_total_requerido}")

st.divider()

# ---- Programación de turnos ----
st.subheader("📅 Generador de Programación de Turnos")

num_semanas = st.number_input("Número de semanas a programar", min_value=1, value=3)

# Definir estructura de turnos
if config_turnos == "3 turnos de 8 horas":
    turnos = ["T1 (8h)", "T2 (8h)", "T3 (8h)"]
else:
    turnos = ["T1 (12h)", "T2 (12h)"]

# Días a programar
semanas = [f"Semana {i+1}" for i in range(num_semanas)]
dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# Crear lista de operadores
operadores = [f"Op{i+1}" for i in range(personal_total_requerido)]

# Total de slots de trabajo a cubrir
slots_totales = num_semanas * len(dias) * len(turnos) * min_operadores_turno

# Generar lista de asignaciones equitativas
asignaciones = list(itertools.cycle(operadores))[:slots_totales]

# DataFrame vacío
columnas = []
for s in semanas:
    for d in dias:
        columnas.append(f"{d} {s}")
programacion = pd.DataFrame(index=operadores, columns=columnas)

# Llenar programación con rotación
indice_asig = 0
for s in semanas:
    for d in dias:
        for t in turnos:
            asignados = asignaciones[indice_asig:indice_asig+min_operadores_turno]
            indice_asig += min_operadores_turno
            for op in asignados:
                programacion.loc[op, f"{d} {s}"] = t

# Llenar descansos
programacion = programacion.fillna("Descanso")

# Calcular total de horas trabajadas
programacion["Total Horas"] = programacion.apply(
    lambda row: sum([horas_por_turno for v in row[:-1] if v != "Descanso"]), axis=1
)

st.dataframe(programacion)

# Descargar en CSV
st.download_button(
    label="⬇️ Descargar programación en CSV",
    data=programacion.to_csv().encode("utf-8"),
    file_name="programacion_turnos.csv",
    mime="text/csv"
)
