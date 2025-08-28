import streamlit as st
import pandas as pd
import math

# -------------------- CONFIGURACIÓN APP --------------------
st.set_page_config(
    page_title="CÁLCULO Y PROGRAMACIÓN DE TURNOS",
    page_icon="📋",
    layout="wide"
)

st.title("📋 CÁLCULO DE PERSONAL Y PROGRAMACIÓN DE TURNOS")
st.caption("Generador de programación automática de turnos en tablas separadas.")

# -------------------- ENTRADAS --------------------
col1, col2 = st.columns(2)

with col1:
    cargo = st.text_input("Nombre del cargo", value="Operador")
    ausentismo_pct = st.number_input("% de ausentismo", 0.0, 100.0, 8.0, step=0.5)
    horas_prom_bisem = st.number_input("Horas por semana (promedio bisemanal)", 10.0, 60.0, 42.0, step=0.5)
    personal_vacaciones = st.number_input("Personal de vacaciones", min_value=0, value=0, step=1)

with col2:
    personas_actuales = st.number_input("Total de personas actuales en el cargo", min_value=0, value=6, step=1)
    dias_cubrir = st.number_input("Días a cubrir en la semana", 1, 7, 7, step=1)
    config_turnos = st.selectbox("Configuración de turnos", ("3 turnos de 8 horas", "2 turnos de 12 horas"))
    dias_vacaciones = st.number_input("Días de vacaciones", min_value=0, value=0, step=1)
    min_operadores_turno = st.number_input("Cantidad mínima de operadores por turno", 1, value=3, step=1)

# -------------------- CONFIGURACIÓN DE TURNOS --------------------
if "3 turnos" in config_turnos:
    n_turnos_dia, horas_por_turno = 3, 8
else:
    n_turnos_dia, horas_por_turno = 2, 12

# -------------------- CÁLCULO DE PERSONAL --------------------
horas_semana_requeridas = dias_cubrir * n_turnos_dia * horas_por_turno * min_operadores_turno
factor_disponibilidad = 1.0 - (ausentismo_pct / 100.0)

if factor_disponibilidad <= 0:
    st.error("El % de ausentismo no puede ser 100% o más.")
    st.stop()

horas_semana_ajustadas = horas_semana_requeridas / factor_disponibilidad
personal_requerido_base = horas_semana_ajustadas / horas_prom_bisem

# Ajuste por vacaciones
horas_vacaciones = personal_vacaciones * dias_vacaciones * horas_por_turno
personal_requerido_vacaciones = horas_vacaciones / horas_prom_bisem

# Total requerido
personal_total_requerido = math.ceil(personal_requerido_base + personal_requerido_vacaciones)
brecha = personal_total_requerido - personas_actuales

# -------------------- RESULTADOS --------------------
st.subheader("📊 Resultados")
st.metric("Personal total necesario", f"{personal_total_requerido}")
st.metric("Brecha de personal (faltante)", f"{brecha}")

st.divider()


# -------------------- PROGRAMACIÓN DE TURNOS --------------------
st.subheader("📅 Programación automática de turnos")

# Lista de operadores calculados
operadores = [f"{cargo} {i+1}" for i in range(personal_total_requerido)]

# Días de la semana (dos semanas ejemplo)
dias_semana = ["Lunes S1", "Martes S1", "Miércoles S1", "Jueves S1", "Viernes S1", "Sábado S1", "Domingo S1",
               "Lunes S2", "Martes S2", "Miércoles S2", "Jueves S2", "Viernes S2", "Sábado S2", "Domingo S2"]

# División de operadores por turno
op_por_turno = personal_total_requerido // n_turnos_dia
sobrantes = personal_total_requerido % n_turnos_dia  # si no es divisible exacto

turnos_dict = {}
for t in range(n_turnos_dia):
    inicio = t * op_por_turno
    fin = inicio + op_por_turno
    if t == n_turnos_dia - 1:  # último turno se lleva los sobrantes
        fin += sobrantes
    turnos_dict[f"Turno {t+1}"] = operadores[inicio:fin]

# Asignación con descanso rotativo
for turno, ops in turnos_dict.items():
    data = {}
    for i, op in enumerate(ops):
        row = []
        for d in range(len(dias_semana)):
            # Selección rotativa: mínimo trabajan, resto descansan
            if (i + d) % len(ops) < min_operadores_turno:
                row.append("Trabajo")
            else:
                row.append("Descanso")
        data[op] = row
    df = pd.DataFrame(data, index=dias_semana).T
    st.write(f"### {turno}")
    st.dataframe(df, use_container_width=True)


