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
st.caption("Versión 2 – Cálculo + programación de operadores por turno.")

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

# Personal base requerido
personal_requerido_base = horas_semana_ajustadas / horas_prom_bisem

# Ajuste por vacaciones
horas_vacaciones = personal_vacaciones * dias_vacaciones * horas_por_turno
personal_requerido_vacaciones = horas_vacaciones / horas_prom_bisem

# Total personal requerido
personal_total_requerido = math.ceil(personal_requerido_base + personal_requerido_vacaciones)
brecha = personal_total_requerido - personas_actuales

# -------------------- RESULTADOS --------------------
st.subheader("Resultados")
st.metric("Personal total necesario", f"{personal_total_requerido}")

st.divider()

# -------------------- PROGRAMACIÓN DE OPERADORES --------------------

import itertools

# -------------------- CALENDARIO 2 SEMANAS --------------------
dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
dias_total = [f"{d} S1" for d in dias_semana] + [f"{d} S2" for d in dias_semana]

# -------------------- GENERAR PROGRAMACIÓN --------------------
def generar_programacion(operadores, config_turnos, min_operadores_turno):
    n_operadores = len(operadores)
    calendario = {op: ["Descanso"] * 14 for op in operadores}

    # Definir cuotas de trabajo por operador
    if "3 turnos" in config_turnos:  # 8h
        cuotas = ["8h"] * 9 + ["12h"]
    else:  # 12h
        cuotas = ["12h"] * 7

    # Repartir turnos de manera rotativa
    asignaciones = list(itertools.cycle(cuotas))
    idx = 0

    for dia in range(14):
        # asignar mínimo de operadores requeridos ese día
        for _ in range(min_operadores_turno):
            op = operadores[idx % n_operadores]
            # buscar la próxima cuota disponible
            while calendario[op][dia] != "Descanso":
                idx += 1
                op = operadores[idx % n_operadores]
            calendario[op][dia] = asignaciones[idx % len(asignaciones)]
            idx += 1

    # Convertir a DataFrame
    df = pd.DataFrame.from_dict(calendario, orient="index", columns=dias_total)
    df.index.name = "Operador"
    df.reset_index(inplace=True)

    return df

# -------------------- RESUMEN POR OPERADOR --------------------
def resumen_operadores(df):
    resumen = []
    for _, row in df.iterrows():
        nombre = row["Operador"]
        valores = list(row.drop("Operador").values)  # asegurar lista
        total_8h = valores.count("8h")
        total_12h = valores.count("12h")
        total_desc = valores.count("Descanso")
        resumen.append({
            "Operador": nombre,
            "Turnos 8h": total_8h,
            "Turnos 12h": total_12h,
            "Descansos": total_desc
        })
    return pd.DataFrame(resumen)

# -------------------- USO --------------------
if personal_total_requerido > 0:
    operadores = [f"Op{i+1}" for i in range(personal_total_requerido)]
    df_programacion = generar_programacion(operadores, config_turnos, min_operadores_turno)

    st.subheader("📅 Calendario de 2 semanas")
    st.dataframe(df_programacion, use_container_width=True)

    # Mostrar resumen
    st.subheader("📊 Resumen de turnos por operador")
    df_resumen = resumen_operadores(df_programacion)
    st.dataframe(df_resumen, use_container_width=True)
else:
    st.info("⚠️ Ingresa parámetros para calcular el personal requerido.")

