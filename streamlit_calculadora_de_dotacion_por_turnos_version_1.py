import streamlit as st
import pandas as pd
import math
import json
import io
from collections import deque

st.set_page_config(page_title="CÁLCULO DE PERSONAL REQUERIDO Y PROGRAMACIÓN DE TURNOS", page_icon="🧮", layout="centered")
st.title("🧮 CÁLCULO DE PERSONAL REQUERIDO Y PROGRAMACIÓN DE TURNOS")
st.caption("Versión 1 – Cálculo mínimo de personal con base en horas requeridas, ausentismo y vacaciones. La rotación y descansos se añadirán en la V2.")

# ---- Sidebar: explicación breve ----
with st.sidebar:
    st.header("¿Cómo funciona?")
    st.write(
        """
        Ingresas los parámetros operativos y la app estima el **número mínimo de personas** necesarias para cubrir los turnos de la semana, **ajustado por ausentismo y vacaciones**.
        
        **Fórmula base semanal:**
        `Horas requeridas = Días a cubrir × Nº turnos × Horas por turno × Mín. operadores por turno`
        
        `Personal requerido = Horas requeridas ajustadas / Horas promedio por trabajador`
        
        Ajuste por ausentismo: divisor `(1 - % ausentismo)`.  
        Ajuste por vacaciones: horas adicionales en función de personas y días fuera.
        """
    )
    st.info("En V2 generaremos un calendario de 4 semanas que cumpla las restricciones de descansos y rotación.")

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
        ("3 turnos de 8 horas", "2 turnos de 12 horas", "4 turnos de 6 horas"),
    )
    dias_vacaciones = st.number_input("Días de vacaciones", min_value=0, value=0, step=1)

min_operadores_turno = st.number_input("Cantidad mínima de operadores por turno", 1, value=3, step=1)

# ---- Configuración de turnos ----
if "3 turnos" in config_turnos:
    n_turnos_dia, horas_por_turno = 3, 8
elif "2 turnos" in config_turnos:
    n_turnos_dia, horas_por_turno = 2, 12
else:
    n_turnos_dia, horas_por_turno = 4, 6

# ---- Cálculos ----
horas_semana_requeridas = dias_cubrir * n_turnos_dia * horas_por_turno * min_operadores_turno
factor_disponibilidad = 1.0 - (ausentismo_pct / 100.0)
if factor_disponibilidad <= 0:
    st.error("El % de ausentismo no puede ser 100% o más.")
    st.stop()

horas_semana_ajustadas = horas_semana_requeridas / factor_disponibilidad

# Personal base requerido
personal_requerido_base = horas_semana_ajustadas / horas_prom_trisem

# Ajuste por vacaciones
if dias_vacaciones is not None:
    horas_vacaciones = personal_vacaciones * dias_vacaciones * 8
else:
    horas_vacaciones = 0
personal_requerido_vacaciones = horas_vacaciones / horas_prom_trisem

# Total personal requerido
personal_total_requerido = math.ceil(personal_requerido_base + personal_requerido_vacaciones)

brecha = personal_total_requerido - personas_actuales

# ---- Resultados ----
st.subheader("Resultados")
met1, met2, met3 = st.columns(3)
met1.metric("Horas/semana a cubrir", f"{horas_semana_requeridas:,.0f}")
met2.metric("Personal adicional requerido (ajustado)", f"{personal_requerido_base + personal_requerido_vacaciones:,.2f}")
met3.metric("Personal total necesario (redondeo)", f"{personal_total_requerido}")

st.divider()

c1, c2 = st.columns(2)
with c1:
    st.markdown("### Resumen de supuestos")
    st.write(
        f"**Cargo:** {cargo}\n\n"
        f"**Esquema de turnos:** {config_turnos} (# turnos/día = {n_turnos_dia}, horas/turno = {horas_por_turno})\n\n"
        f"**Días a cubrir/semana:** {dias_cubrir}\n\n"
        f"**Mín. operadores por turno:** {min_operadores_turno}\n\n"
        f"**% Ausentismo:** {ausentismo_pct:.1f}%\n\n"
        f"**Horas promedio/semana por trabajador (trisemanal):** {horas_prom_trisem}\n\n"
        f"**Personal de vacaciones:** {personal_vacaciones} personas, {dias_vacaciones} días"
    )

with c2:
    st.markdown("### Comparación con dotación actual")
    st.write(f"**Personas actuales:** {personas_actuales}")
    if brecha > 0:
        st.warning(f"⛑️ Faltan **{brecha}** personas para cumplir el requerimiento.")
    elif brecha < 0:
        st.success(f"✅ Tienes **{-brecha}** personas por encima del mínimo requerido.")
    else:
        st.info("⚖️ La dotación actual coincide exactamente con el mínimo requerido.")

st.divider()
st.markdown(
    """
    #### Notas
    - Incluye ajuste por ausentismo y por vacaciones.
    - La V2 generará calendario de 4 semanas con descansos y rotación de turnos.
    """
)

# ---- Descarga (JSON) ----
payload = {
    "cargo": cargo,
    "%_ausentismo": ausentismo_pct,
    "horas_prom_semana_trisem": horas_prom_trisem,
    "personas_actuales": personas_actuales,
    "dias_cubrir_semana": dias_cubrir,
    "config_turnos": config_turnos,
    "n_turnos_dia": n_turnos_dia,
    "horas_por_turno": horas_por_turno,
    "min_operadores_por_turno": min_operadores_turno,
    "personal_vacaciones": personal_vacaciones,
    "dias_vacaciones": dias_vacaciones,
    "personal_requerido_base": round(personal_requerido_base, 2),
    "personal_requerido_vacaciones": round(personal_requerido_vacaciones, 2),
    "personal_total_requerido": personal_total_requerido,
    "brecha_vs_actual": brecha,
}
st.download_button(
    label="⬇️ Descargar resultados (JSON)",
    data=json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
    file_name="resultado_personal_v1.json",
    mime="application/json",
)

# ---
# Lógica de programación de turnos
import streamlit as st
import pandas as pd
import itertools

# ------------------- CONFIGURACIÓN ------------------- #
st.title("Generador de Programación de Turnos")

# Entradas del usuario
num_operadores = st.number_input("Número total de operadores", min_value=1, value=26)
operadores_por_turno = st.number_input("Operadores por turno", min_value=1, value=6)
modelo = st.radio("Modelo de turnos", ["128 horas (8h)", "124 horas (12h)"])
num_semanas = st.number_input("Número de semanas a programar", min_value=1, value=3)

# Definir estructura de turnos según modelo
if modelo == "128 horas (8h)":
    turnos = ["T1 (8h)", "T2 (8h)", "T3 (8h)"]
    horas_turno = 8
else:
    turnos = ["T1 (12h)", "T2 (12h)"]
    horas_turno = 12

# Días a programar
semanas = [f"Semana {i+1}" for i in range(num_semanas)]
dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# Crear lista de operadores
operadores = [f"Op{i+1}" for i in range(num_operadores)]

# Total de slots de trabajo a cubrir
slots_totales = num_semanas * len(dias) * len(turnos) * operadores_por_turno

# Generar lista de asignaciones equitativas (rotación)
asignaciones = list(itertools.cycle(operadores))[:slots_totales]

# DataFrame vacío para la programación
columnas = []
for s in semanas:
    for d in dias:
        columnas.append(f"{d} {s}")
programacion = pd.DataFrame(index=operadores, columns=columnas)

# Llenar programación con rotación equitativa
indice_asig = 0
for s in semanas:
    for d in dias:
        for t in turnos:
            asignados = asignaciones[indice_asig:indice_asig+operadores_por_turno]
            indice_asig += operadores_por_turno
            for op in asignados:
                if pd.isna(programacion.loc[op, f"{d} {s}"]):
                    programacion.loc[op, f"{d} {s}"] = t

# Llenar descansos donde no se asignó turno
programacion = programacion.fillna("Descanso")

# Calcular total de horas trabajadas
programacion["Total Horas"] = programacion.apply(
    lambda row: sum([horas_turno for v in row[:-1] if v != "Descanso"]), axis=1
)

# Mostrar resultados
st.subheader("Programación de Turnos")
st.dataframe(programacion)

# Descargar en Excel
st.download_button(
    label="Descargar programación en Excel",
    data=programacion.to_csv().encode("utf-8"),
    file_name="programacion_turnos.csv",
    mime="text/csv"
)
