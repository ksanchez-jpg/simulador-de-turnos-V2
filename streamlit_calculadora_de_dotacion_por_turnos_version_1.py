import math
import streamlit as st

# ---------------------------------------------
# Calculadora de dotación mínima por turnos
# Versión 1: Cálculo de personas necesarias (sin generar calendario)
# ---------------------------------------------
# Próximas versiones (V2+):
# - Generación de calendario 4 semanas cumpliendo:
#   * Promedio trisemanal de 42 h por trabajador
#   * 1 domingo libre en 4 semanas
#   * Rotación secuencial de turnos con día de descanso previo al cambio
#   * Días de descanso variados por persona
# ---------------------------------------------

st.set_page_config(page_title="Calculadora de Dotación por Turnos", page_icon="🧮", layout="centered")
st.title("🧮 Calculadora de Dotación por Turnos")
st.caption("Versión 1 – Cálculo mínimo de personal con base en horas requeridas y ausentismo. La rotación y descansos se añadirán en la V2.")

# ---- Sidebar: explicación breve ----
with st.sidebar:
    st.header("¿Cómo funciona?")
    st.write(
        """
        Ingresas los parámetros operativos y la app estima el **número mínimo de personas** (FTE)
        necesarias para cubrir los turnos de la semana, **ajustado por ausentismo**.
        \n\nFórmula base semanal:
        
        `Horas requeridas = Días a cubrir × Nº turnos × Horas por turno × Mín. operadores por turno`
        
        `Personas requeridas (FTE) = Horas requeridas ajustadas / Horas promedio por trabajador`
        
        El ajuste por ausentismo se realiza dividiendo por `(1 - % ausentismo)`.
        """
    )
    st.info("En V2 generaremos un calendario de 4 semanas que cumpla las restricciones de descansos y rotación.")

# ---- Entradas ----
col1, col2 = st.columns(2)
with col1:
    cargo = st.text_input("Nombre del cargo", value="Operador")
    ausentismo_pct = st.number_input("% de ausentismo", min_value=0.0, max_value=100.0, value=8.0, step=0.5, help="Porcentaje promedio de ausencias (incapacidades, vacaciones, permisos, etc.)")
    horas_prom_trisem = st.number_input("Horas por semana (promedio trisemanal)", min_value=10.0, max_value=60.0, value=42.0, step=0.5, help="Promedio semanal de horas por trabajador, medido sobre 3 semanas. Ej: 42 h.")

with col2:
    personas_actuales = st.number_input("Total de personas actuales en el cargo", min_value=0, value=0, step=1)
    dias_cubrir = st.number_input("Días a cubrir en la semana", min_value=1, max_value=7, value=7, step=1)
    config_turnos = st.selectbox(
        "Configuración de turnos",
        (
            "3 turnos de 8 horas",
            "2 turnos de 12 horas",
            "4 turnos de 6 horas",
        ),
        help="Selecciona el esquema de turnos a cubrir por día"
    )

min_operadores_turno = st.number_input("Cantidad mínima de operadores por turno", min_value=1, value=3, step=1)

# ---- Decodificar configuración de turnos ----
if "3 turnos" in config_turnos:
    n_turnos_dia = 3
    horas_por_turno = 8
elif "2 turnos" in config_turnos:
    n_turnos_dia = 2
    horas_por_turno = 12
else:  # "4 turnos de 6 horas"
    n_turnos_dia = 4
    horas_por_turno = 6

# ---- Cálculos ----
# Horas semanales totales a cubrir (operator-hours)
horas_semana_requeridas = dias_cubrir * n_turnos_dia * horas_por_turno * min_operadores_turno

# Ajuste por ausentismo
factor_disponibilidad = 1.0 - (ausentismo_pct / 100.0)
if factor_disponibilidad <= 0:
    st.error("El % de ausentismo no puede ser 100% o más. Ajusta el valor.")
    st.stop()

horas_semana_ajustadas = horas_semana_requeridas / factor_disponibilidad

# Personas requeridas (FTE) según horas disponibles por trabajador
if horas_prom_trisem <= 0:
    st.error("Las horas promedio por semana deben ser mayores que 0.")
    st.stop()

fte_requeridos = horas_semana_ajustadas / horas_prom_trisem
personas_necesarias = math.ceil(fte_requeridos)

# Brecha vs. dotación actual
brecha = personas_necesarias - personas_actuales

# ---- Resultados ----
st.subheader("Resultados")
met1, met2, met3 = st.columns(3)
met1.metric("Horas/semana a cubrir", f"{horas_semana_requeridas:,.0f}")
met2.metric("FTE requeridos (ajustado)", f"{fte_requeridos:,.2f}")
met3.metric("Personas necesarias (redondeo)", f"{personas_necesarias}")

st.divider()

c1, c2 = st.columns(2)
with c1:
    st.markdown("### Resumen de supuestos")
    st.write(
        f"**Cargo:** {cargo}\n\n"
        f"**Esquema de turnos:** {config_turnos} (\# turnos/día = {n_turnos_dia}, horas/turno = {horas_por_turno})\n\n"
        f"**Días a cubrir/semana:** {dias_cubrir}\n\n"
        f"**Mín. operadores por turno:** {min_operadores_turno}\n\n"
        f"**% Ausentismo:** {ausentismo_pct:.1f}%\n\n"
        f"**Horas promedio/semana por trabajador (trisemanal):** {horas_prom_trisem}"
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
    - Este cálculo asume **cobertura total** de los turnos seleccionados todos los días elegidos.
    - El ausentismo se aplica como un **factor de disponibilidad** (divisor), por lo que incrementa las horas
      a cubrir para determinar la dotación mínima necesaria.
    - La V2 generará un **calendario de 4 semanas** que cumpla: 1 domingo libre por persona, rotación de turnos
      con un día de descanso previo al cambio y variación de días de descanso.
    """
)

# ---- Descarga de parámetros y resultado (opcional) ----
import json
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
    "horas_semana_requeridas": horas_semana_requeridas,
    "horas_semana_ajustadas": horas_semana_ajustadas,
    "fte_requeridos": round(fte_requeridos, 2),
    "personas_necesarias": personas_necesarias,
    "brecha_vs_actual": brecha,
}

st.download_button(
    label="⬇️ Descargar resultados (JSON)",
    data=json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
    file_name="resultado_dotacion_v1.json",
    mime="application/json",
)

