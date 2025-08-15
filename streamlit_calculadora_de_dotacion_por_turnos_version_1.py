import math
import streamlit as st
import json
import pandas as pd
import numpy as np

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
    - La V2 generará calendario de 4 semanas con descansos y rotación de turnos.
    """
)

# ---- Descarga ----
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

# =========================================================================
# ---- Sección de funcionalidad adicional: Programación de Turnos (V2) ----
# =========================================================================

st.divider()
st.header("🗓️ Programación de Turnos (Versión V2)")
st.info("Esta programación de 4 semanas muestra la rotación de turnos y los días de descanso.")

# Generar una lista de días del mes (4 semanas)
dias_del_mes = [f"Día {i+1}" for i in range(28)]

# Generar una lista de turnos
turnos = [f"Turno {i+1}" for i in range(n_turnos_dia)]

# Crear una lista de personal con nombres genéricos
personal = [f"{cargo} {i+1}" for i in range(personal_total_requerido)]

# Calcular el número de operadores adicionales necesarios (un extra por cada 7 días cubiertos)
num_adicional = math.ceil(personal_total_requerido / 7) if dias_cubrir == 7 else math.ceil(personal_total_requerido / dias_cubrir)
personal_adicional = [f"OP-AD {i+1}" for i in range(num_adicional)]

# Crear un DataFrame para la programación completa
programacion_df = pd.DataFrame(index=personal + personal_adicional, columns=dias_del_mes)
programacion_df = programacion_df.fillna("")

# Lógica de asignación de turnos y descansos
# Asumimos una rotación simple: un día de descanso cada 7 días.
for i, persona in enumerate(personal):
    for dia_idx in range(28):
        dia = dias_del_mes[dia_idx]
        
        # Asignar un día de descanso rotativo cada 7 días
        if (dia_idx + i) % 7 == 0:
            programacion_df.loc[persona, dia] = "descansa"
            # Asignar operador adicional para cubrir el descanso
            op_adicional_idx = i % len(personal_adicional)
            programacion_df.loc[personal_adicional[op_adicional_idx], dia] = "Cubre descanso"
        else:
            # Asignar turnos de manera rotativa
            turno_idx = (dia_idx + i) % n_turnos_dia
            programacion_df.loc[persona, dia] = turnos[turno_idx]

# Dividir la tabla en subtipos según los turnos
programacion_por_turno = {turno: pd.DataFrame(index=[], columns=dias_del_mes) for turno in turnos}
for turno in turnos:
    programacion_por_turno[turno] = pd.DataFrame(index=programacion_df.index, columns=dias_del_mes)
    programacion_por_turno[turno] = programacion_por_turno[turno].fillna("")

# Llenar las tablas de cada turno
for persona_idx, persona in enumerate(programacion_df.index):
    for dia_idx, dia in enumerate(dias_del_mes):
        valor = programacion_df.loc[persona, dia]
        if "Turno" in valor:
            turno_asignado = valor
            programacion_por_turno[turno_asignado].loc[persona, dia] = "X"
        elif "descansa" in valor:
            # Asignar el día de descanso en la tabla correspondiente
            # En este caso, lo ponemos en la tabla del turno del primer día para visualización
            if "Turno" in programacion_df.loc[persona, dias_del_mes[0]]:
                primer_turno_asignado = programacion_df.loc[persona, dias_del_mes[0]]
                programacion_por_turno[primer_turno_asignado].loc[persona, dia] = "descansa"
        elif "Cubre descanso" in valor:
             # Asignar el reemplazo en la tabla del turno que cubre
            if persona.startswith("OP-AD"):
                # Asumimos que los OP-AD cubren el turno del operador principal al que reemplazan
                op_principal_idx = persona_idx
                if op_principal_idx < len(personal):
                    turno_cubierto = programacion_df.loc[personal[op_principal_idx], dias_del_mes[(dia_idx-1+28)%28]]
                    if "Turno" in turno_cubierto:
                        programacion_por_turno[turno_cubierto].loc[persona, dia] = "Cubre"

# Mostrar las tablas
for turno, df in programacion_por_turno.items():
    # Limpiar filas vacías para una mejor presentación
    df_limpio = df[df.apply(lambda row: any(row), axis=1)]
    if not df_limpio.empty:
        st.subheader(f"Programación {turno}")
        st.dataframe(df_limpio)
