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
# ---- Programación de turnos corregida: 1 turno por día y división equitativa (round-robin) ----
st.subheader("📋 Programación de turnos (restricción: 1 turno por día)")

if personal_total_requerido <= 0:
    st.info("No hay personal requerido calculado para generar la programación.")
else:
    # Lista global de operadores
    operadores = [f"op{i+1}" for i in range(personal_total_requerido)]

    # Número de turnos a dividir
    k = n_turnos_dia

    # Distribución round-robin: garantiza que cada operador quede en UN solo turno
    grupos_turnos = [[] for _ in range(k)]
    for idx, op in enumerate(operadores):
        grupos_turnos[idx % k].append(op)

    # Mostrar resumen de la división (número de operadores por turno y listado)
    resumen_counts = {f"Turno {t+1}": len(grupos_turnos[t]) for t in range(k)}
    st.write("**Distribución equitativa de operadores por turno (round-robin):**")
    st.write(resumen_counts)
    # opcional mostrar detalle
    for t in range(k):
        st.write(f"Turno {t+1}: {grupos_turnos[t]}")

    # Parámetros para generar la matriz de 4 semanas
    semanas = 4
    dias_semana = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

    # Patrón de trabajo/descanso: 5 días ON / 2 días OFF (configurable)
    patron_base = [1, 1, 1, 1, 1, 0, 0]  # 1 = trabaja, 0 = descansa

    # Generar una tabla independiente por cada turno (solo con sus operadores)
    for t in range(k):
        turno_num = t + 1
        ops = grupos_turnos[t]

        st.markdown(f"### 🔹 Turno {turno_num} — Operadores asignados: {len(ops)}")
        if len(ops) == 0:
            st.warning(f"Turno {turno_num} no tiene operadores asignados.")
            continue

        # Construir columnas: "Operador" + cada día de cada semana
        data = {"Operador": ops}
        for semana in range(1, semanas + 1):
            for dia in dias_semana:
                col_name = f"{dia} semana {semana}"
                asignaciones = []
                # índice absoluto del día (0..27) para rotación
                for i, op in enumerate(ops):
                    # Desfase por operador para escalonar descansos
                    offset = i % len(patron_base)
                    dia_index = ((semana - 1) * len(dias_semana) + dias_semana.index(dia))  # 0..27
                    pos = (offset + dia_index) % len(patron_base)
                    if patron_base[pos] == 1:
                        asignaciones.append(f"Turno {turno_num}")
                    else:
                        asignaciones.append("Descansa")
                data[col_name] = asignaciones

        # Crear DataFrame y mostrar
        df_turno = pd.DataFrame(data)
        # Asegurar que 'Operador' sea la primera columna
        cols = df_turno.columns.tolist()
        if cols[0] != "Operador":
            cols.remove("Operador")
            cols.insert(0, "Operador")
            df_turno = df_turno[cols]

        st.dataframe(df_turno, use_container_width=True)

    st.info(
        "Reglas aplicadas:\n"
        "- Cada operador está asignado exclusivamente a un turno (aparece solo en la tabla de ese turno).\n"
        "- La distribución se hizo con round-robin para evitar agrupaciones y asegurar equidad.\n"
        "- Patrón de trabajo/descanso por operador: 5 días ON / 2 días OFF, desfasado por operador."
    )
