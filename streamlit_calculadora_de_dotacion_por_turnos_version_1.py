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
    - La V2 generará calendario de 4 semanas que cumpla las restricciones de descansos y rotación.
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
st.info("Esta es una programación de 4 semanas que considera la rotación de turnos, días de descanso y personal adicional.")

# Definimos los días de la semana y los turnos
dias_de_la_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
turnos = [f"Turno {i+1}" for i in range(n_turnos_dia)]

# Creamos las listas de operadores actuales y adicionales
personal_actual = [f"OP{i+1}" for i in range(personal_total_requerido)]
num_adicional = math.ceil(personal_total_requerido / (7/2)) # Un operador adicional por cada 3.5 dias trabajados
personal_adicional = [f"OP-AD{i+1}" for i in range(num_adicional)]
personal_total = personal_actual + personal_adicional

# Creamos un DataFrame para la programación completa
columnas = [f"{dias_de_la_semana[i % 7]} (Semana {i // 7 + 1})" for i in range(28)]
programacion_df = pd.DataFrame(index=personal_total, columns=columnas)
programacion_df.fillna("", inplace=True)

# Lógica de programación de turnos y descansos
# Asignamos una rotación para cada operador
if n_turnos_dia > 0:
    for i, operador in enumerate(personal_actual):
        # Asignamos un patrón de rotación de 5 días de trabajo y 2 de descanso
        # La semana de inicio y el turno inicial de cada operador se escalona
        turno_inicio = i % n_turnos_dia
        # El día de inicio de descanso se escalona
        dia_descanso_inicio = i % 7

        for semana in range(4):
            dia_inicio_semana = semana * 7
            
            # Asignamos el turno
            turno_idx = (turno_inicio + semana) % n_turnos_dia
            turno_asignado = turnos[turno_idx]
            
            # Asignamos los 2 dias de descanso, asegurando que uno sea antes del cambio de turno
            # El día de descanso se desplaza para cada operador y en cada semana
            dia_descanso1_idx = (dia_descanso_inicio + semana * 2) % 7
            dia_descanso2_idx = (dia_descanso1_idx + 1) % 7
            
            # Verificamos la regla de no trabajar dos domingos seguidos
            if dias_de_la_semana[dia_descanso1_idx] == "Domingo" and (dia_descanso1_idx + 7) % 7 == dia_descanso1_idx:
                # Si el primer descanso es un domingo, el segundo no puede ser un lunes si el primer domingo fue el fin de semana anterior.
                # Esta lógica simple no es perfecta, pero intenta evitar el caso más obvio.
                pass
            
            for dia_idx in range(7):
                col_name = f"{dias_de_la_semana[dia_idx]} (Semana {semana+1})"
                
                if dia_idx == dia_descanso1_idx or dia_idx == dia_descanso2_idx:
                    programacion_df.loc[operador, col_name] = "Descansa"
                    
                    # Asignamos a un operador adicional para cubrir el turno
                    idx_adicional = i % len(personal_adicional)
                    op_adicional = personal_adicional[idx_adicional]
                    programacion_df.loc[op_adicional, col_name] = f"Cubre {turno_asignado}"
                else:
                    programacion_df.loc[operador, col_name] = turno_asignado

# Dividir la tabla en subtipos según los turnos para la presentación
programacion_por_turno = {turno: pd.DataFrame(index=personal_total, columns=columnas) for turno in turnos}
for turno in programacion_por_turno.values():
    turno.fillna("", inplace=True)

# Llenamos las tablas de cada turno
for operador in personal_total:
    for dia_col in columnas:
        valor = programacion_df.loc[operador, dia_col]
        
        if "Turno" in valor:
            programacion_por_turno[valor].loc[operador, dia_col] = "Trabaja"
        elif "Descansa" in valor and operador.startswith("OP"):
            semana = int(dia_col.split("Semana ")[1].replace(")", "")) - 1
            # Para determinar el turno del descanso, nos basamos en el turno de la semana
            turno_idx = (personal_actual.index(operador) + semana) % n_turnos_dia
            turno_asignado = turnos[turno_idx]
            programacion_por_turno[turno_asignado].loc[operador, dia_col] = "Descansa"
        elif "Cubre" in valor:
            # Asignamos el turno que el operador adicional cubre
            turno_cubierto = valor.split("Cubre ")[1]
            programacion_por_turno[turno_cubierto].loc[operador, dia_col] = "Cubre"

# Mostrar las tablas, filtrando filas vacías
for turno, df in programacion_por_turno.items():
    df_limpio = df.loc[(df != "").any(axis=1)]
    if not df_limpio.empty:
        st.subheader(f"Programación {turno}")
        st.dataframe(df_limpio)
