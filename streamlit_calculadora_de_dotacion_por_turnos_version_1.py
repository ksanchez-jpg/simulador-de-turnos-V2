import streamlit as st
import pandas as pd
import math
import json

st.set_page_config(
    page_title="CÁLCULO DE PERSONAL REQUERIDO",
    page_icon="🧮",
    layout="centered"
)
st.title("🧮 CÁLCULO DE PERSONAL REQUERIDO")
st.caption("Versión 1 – Cálculo mínimo de personal con base en horas requeridas, ausentismo y vacaciones.")

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
horas_vacaciones = personal_vacaciones * dias_vacaciones * horas_por_turno
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
    """
)


# ---- Programación de Turnos ---- parte a cambiar y modificar
import streamlit as st
import pandas as pd

# ============================
# Entradas del usuario
# ============================
st.title("Simulador de Programación de Turnos")

personal_total_requerido = st.number_input("Número total de operadores requeridos", min_value=1, value=12)
num_turnos = st.number_input("Número de turnos", min_value=1, value=3)
min_operadores_turno = st.number_input("Cantidad mínima de operadores por turno", min_value=1, value=4)

# ============================
# División de operadores por turno (semana base)
# ============================
operadores = [f"OP{i+1}" for i in range(personal_total_requerido)]
grupo_por_turno = {}

if num_turnos > 0:
    tam_grupo = personal_total_requerido // num_turnos
    for turno in range(1, num_turnos + 1):
        inicio = (turno - 1) * tam_grupo
        fin = turno * tam_grupo
        grupo_por_turno[turno] = operadores[inicio:fin]

# ============================
# Programación de turnos para un mes
# ============================
st.subheader("Programación mensual de turnos")

dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
num_semanas = 4  # asumimos 1 mes = 4 semanas

# Generar tablas por cada turno
for turno_inicial, operadores_turno in grupo_por_turno.items():
    st.write(f"### Programación de grupo que inicia en Turno {turno_inicial}")
    
    programacion = pd.DataFrame(index=operadores_turno)
    total_op = len(operadores_turno)

    for semana in range(1, num_semanas + 1):
        # Calcular turno que corresponde esa semana por rotación
        turno_semana = ((turno_inicial - 1 + (semana - 1)) % num_turnos) + 1

        for dia in dias_semana:
            col = f"{dia} - Semana {semana}"
            asignaciones = []

            for i, op in enumerate(operadores_turno):
                asignacion = f"Turno {turno_semana}"

                # Reglas de descanso en cambio de turno
                if dia == "Domingo" and semana < num_semanas:
                    # Mitad del grupo descansa el domingo antes del cambio
                    if i >= min_operadores_turno:
                        asignacion = "Descansa"
                elif dia == "Lunes" and semana > 1:
                    # Mitad del grupo que sí trabajó domingo descansa lunes
                    if i < total_op - min_operadores_turno:
                        asignacion = "Descansa"

                asignaciones.append(asignacion)

            # Asegurar que siempre hay al menos el mínimo de operadores trabajando
            trabajando = sum(1 for a in asignaciones if a.startswith("Turno"))
            if trabajando < min_operadores_turno:
                # Si no alcanza, mover algunos descansos a trabajar
                for j in range(len(asignaciones)):
                    if asignaciones[j] == "Descansa" and trabajando < min_operadores_turno:
                        asignaciones[j] = f"Turno {turno_semana}"
                        trabajando += 1

            programacion[col] = asignaciones

    st.dataframe(programacion)
