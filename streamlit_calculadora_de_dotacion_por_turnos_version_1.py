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
    min_operadores_turno = st.number_input("Cantidad mínima de operadores por turno", 1, value=6, step=1)
    
    st.write("---")
    st.subheader("Configuración de Turnos por Día")
    dias_con_turno_12h = st.number_input("Días con turnos de 12 horas", min_value=0, max_value=dias_cubrir, value=2, step=1)
    dias_con_turno_8h = dias_cubrir - dias_con_turno_12h
    st.write(f"Días con turnos de 8 horas: {dias_con_turno_8h}")

# ---- Cálculos ----
horas_requeridas_12h = dias_con_turno_12h * 2 * 12 * min_operadores_turno
horas_requeridas_8h = dias_con_turno_8h * 3 * 8 * min_operadores_turno

horas_semana_requeridas = horas_requeridas_12h + horas_requeridas_8h
factor_disponibilidad = 1.0 - (ausentismo_pct / 100.0)
if factor_disponibilidad <= 0:
    st.error("El % de ausentismo no puede ser 100% o más.")
    st.stop()

horas_semana_ajustadas = horas_semana_requeridas / factor_disponibilidad

personal_requerido_base = horas_semana_ajustadas / horas_prom_trisem
horas_vacaciones = personal_vacaciones * dias_vacaciones * 8 # Asumiendo 8h/dia
personal_requerido_vacaciones = horas_vacaciones / horas_prom_trisem
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
        f"**Días a cubrir/semana:** {dias_cubrir}\n\n"
        f"**Días con turnos de 12h:** {dias_con_turno_12h} (2 turnos)\n\n"
        f"**Días con turnos de 8h:** {dias_con_turno_8h} (3 turnos)\n\n"
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
    "dias_12h": dias_con_turno_12h,
    "dias_8h": dias_con_turno_8h,
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
# ---

def weekly_days_pattern(horas_turno:int):
    if horas_turno == 12:
        return [4, 3, 4, 3]
    elif horas_turno == 8:
        return [6, 5, 5, 5]
    else: # 6 hours
        return [7, 7, 7, 7]

st.write("---")
st.header("3. Programación de Turnos (4 Semanas)")

if st.button("Generar Programación de Turnos", key='generate_schedule_btn'):
    
    all_operators = []
    for i in range(personas_actuales):
        all_operators.append(f"OP-{i+1}")
    for i in range(personal_total_requerido - personas_actuales):
        all_operators.append(f"OP-AD-{i+1}")
    
    if not all_operators:
        st.warning("No se puede generar la programación sin personal. Por favor, ajusta los valores de entrada.")
        st.stop()
    
    operator_schedules = {op_id: [""] * 28 for op_id in all_operators}
    
    day_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    
    # NEW LOGIC: Determine which days have 12h shifts and which have 8h shifts
    shift_duration_per_day = {}
    twelve_hour_shift_days = ['Turno 1 (12h)', 'Turno 2 (12h)']
    eight_hour_shift_days = ['Turno 1 (8h)', 'Turno 2 (8h)', 'Turno 3 (8h)']

    for day_idx in range(dias_con_turno_12h):
        shift_duration_per_day[day_names[day_idx]] = {'hours': 12, 'shifts': 2}
    for day_idx in range(dias_con_turno_12h, dias_cubrir):
        shift_duration_per_day[day_names[day_idx]] = {'hours': 8, 'shifts': 3}

    for op_idx, op_id in enumerate(all_operators):
        current_shift_rotation = op_idx % 3
        stagger_offset = op_idx % 7
        
        for week in range(4):
            for day_idx in range(7):
                global_day_index = week * 7 + day_idx
                day_name = day_names[day_idx]

                if day_idx >= dias_cubrir:
                    operator_schedules[op_id][global_day_index] = "DESCANSA"
                    continue
                
                hours_per_shift_for_day = shift_duration_per_day[day_name]['hours']
                shifts_per_day = shift_duration_per_day[day_name]['shifts']
                
                assigned_shift = f"Turno {((op_idx + week) % shifts_per_day) + 1} ({hours_per_shift_for_day}h)"
                
                operator_schedules[op_id][global_day_index] = assigned_shift

    all_schedules_data = {}

    operators_per_shift_group = [math.floor(personal_total_requerido / 3)] * 3
    remainder = personal_total_requerido % 3
    if remainder > 0:
        operators_per_shift_group[1] += remainder

    op_start_index = 0
    for shift_index in range(3):
        shift_name = f"Turno {shift_index+1}"
        num_ops_in_group = operators_per_shift_group[shift_index]
        
        group_operators = all_operators[op_start_index:op_start_index + num_ops_in_group]
        
        current_shift_schedule_data = {}
        for op_id in group_operators:
            current_shift_schedule_data[op_id] = operator_schedules[op_id]

        df_shift = pd.DataFrame(current_shift_schedule_data, index=[f"Semana {w+1} | {day}" for w in range(4) for day in day_names]).T
        
        st.subheader(f"Programación para {shift_name} | Operadores: {num_ops_in_group}")
        st.dataframe(df_shift)
        all_schedules_data[shift_name] = df_shift
        
        op_start_index += num_ops_in_group

    st.write("---")
    st.subheader("Descargar Programación Completa")
    st.write("Haz clic en el botón para descargar la programación de todos los turnos en un archivo de Excel.")

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for shift_name, df_shift in all_schedules_data.items():
            df_shift.to_excel(writer, sheet_name=shift_name)
    
    output.seek(0)

    st.download_button(
        label="Descargar Horario a Excel",
        data=output,
        file_name='programacion_turnos.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
