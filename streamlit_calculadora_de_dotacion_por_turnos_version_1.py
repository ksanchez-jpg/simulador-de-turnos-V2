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
import pandas as pd
import numpy as np

def generar_programacion(operadores, tipo_turno):
    """
    Genera programación de 2 semanas para los operadores.
    - operadores: lista con nombres o cantidad de operadores
    - tipo_turno: "8h" o "12h"
    """
    if isinstance(operadores, int):
        operadores = [f"Operador {i+1}" for i in range(operadores)]

    num_ops = len(operadores)
    dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

    programacion = []

    if tipo_turno == "8h":
        # Semana 1 → 6x8h
        for i, op in enumerate(operadores):
            descanso = i % 7  # descanso rotativo
            semana = [8 if d != descanso else 0 for d in range(7)]
            programacion.append({"Operador": op, "Semana": 1, "Turnos": semana})

        # Semana 2 → 3x8h + 1x12h
        for i, op in enumerate(operadores):
            descansos = [(i+1) % 7, (i+2) % 7, (i+3) % 7]  # rotación de descansos
            semana = [0]*7
            horas_asignadas = 0
            for d in range(7):
                if d not in descansos and horas_asignadas < 36:
                    semana[d] = 8
                    horas_asignadas += 8
            # Asignar el día de 12h (si sobra)
            if horas_asignadas < 42:
                for d in range(7):
                    if semana[d] == 0:
                        semana[d] = 12
                        break
            programacion.append({"Operador": op, "Semana": 2, "Turnos": semana})

    elif tipo_turno == "12h":
        # Semana 1 → 4x12h
        for i, op in enumerate(operadores):
            descanso = [i % 7, (i+2) % 7, (i+4) % 7]  # descansos rotativos
            semana = [12 if d not in descanso else 0 for d in range(7)]
            programacion.append({"Operador": op, "Semana": 1, "Turnos": semana})

        # Semana 2 → 3x12h
        for i, op in enumerate(operadores):
            trabajo = [(i+1) % 7, (i+3) % 7, (i+5) % 7]  # rotación distinta
            semana = [12 if d in trabajo else 0 for d in range(7)]
            programacion.append({"Operador": op, "Semana": 2, "Turnos": semana})

    # Pasar a DataFrame
    data = []
    for row in programacion:
        for d, h in zip(dias, row["Turnos"]):
            data.append([row["Operador"], row["Semana"], d, h])

    df = pd.DataFrame(data, columns=["Operador", "Semana", "Día", "Horas"])
    return df


# --- EJEMPLO DE USO EN STREAMLIT ---
import streamlit as st

st.subheader("📅 Programación de Turnos")

num_operadores = st.number_input("Número de operadores", min_value=1, value=5)
tipo_turno = st.radio("Tipo de turno", ["8h", "12h"])

if st.button("Generar Programación"):
    df_prog = generar_programacion(num_operadores, tipo_turno)
    st.dataframe(df_prog)

