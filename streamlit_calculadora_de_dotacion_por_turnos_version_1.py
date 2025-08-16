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
# ---

def weekly_days_pattern(horas_turno:int):
    if horas_turno == 12:
        return [4, 3, 4, 3]
    elif horas_turno == 8:
        return [6, 5, 5, 5]
    else: # 6 hours
        return [7, 7, 7, 7]

def check_trisem_42(hours_weeks, horas_turno):
    tol = horas_turno
    ok13 = abs(sum(hours_weeks[0:3]) - 126) <= tol
    ok24 = abs(sum(hours_weeks[1:4]) - 126) <= tol
    return ok13 and ok24, (sum(hours_weeks[0:3]) - 126, sum(hours_weeks[1:4]) - 126)

st.write("---")
st.header("3. Programación de Turnos (4 Semanas)")

if st.button("Generar Programación de Turnos", key='generate_schedule_btn'):
    
    # 1. Preparar la lista de operadores
    all_operators = []
    for i in range(personas_actuales):
        all_operators.append(f"OP-{i+1}")
    for i in range(personal_total_requerido - personas_actuales):
        all_operators.append(f"OP-AD-{i+1}")
    
    if not all_operators:
        st.warning("No se puede generar la programación sin personal. Por favor, ajusta los valores de entrada.")
        st.stop()
    
    # 2. Generar horarios para cada operador
    operator_schedules = {op_id: [""] * 28 for op_id in all_operators}
    
    work_days_patterns = weekly_days_pattern(horas_por_turno)
    day_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    
    for op_idx, op_id in enumerate(all_operators):
        current_shift_rotation = op_idx % n_turnos_dia
        stagger_offset = op_idx % 7
        
        for week in range(4):
            days_to_work = work_days_patterns[week]
            
            # Check rest day before shift change
            rest_before_change = False
            if week > 0:
                prev_week_last_day_status = operator_schedules[op_id][(week-1)*7+6]
                if prev_week_last_day_status != "DESCANSA":
                    rest_before_change = True

            # Assign shifts for the entire week
            assigned_shift = f"Turno {((week + current_shift_rotation) % n_turnos_dia) + 1}"
            
            for day_idx in range(7):
                global_day_index = week * 7 + day_idx
                
                # Enforce rest on Monday after a work-filled Sunday
                if rest_before_change and day_idx == 0:
                    operator_schedules[op_id][global_day_index] = "DESCANSA"
                    continue
                
                # Normal work/rest assignment
                day_in_rotation = (day_idx + stagger_offset) % 7
                
                if day_in_rotation < days_to_work:
                    operator_schedules[op_id][global_day_index] = assigned_shift
                else:
                    operator_schedules[op_id][global_day_index] = "DESCANSA"

    all_schedules_data = {}

    # 3. Organizar los horarios por grupo de turno y verificar cobertura
    operators_per_shift_group = [math.floor(personal_total_requerido / n_turnos_dia)] * n_turnos_dia
    remainder = personal_total_requerido % n_turnos_dia
    if remainder > 0:
        if n_turnos_dia >= 2:
            operators_per_shift_group[1] += remainder
        else:
            operators_per_shift_group[0] += remainder

    op_start_index = 0
    for shift_index in range(n_turnos_dia):
        shift_name = f"Turno {shift_index+1}"
        num_ops_in_group = operators_per_shift_group[shift_index]
        
        group_operators = all_operators[op_start_index:op_start_index + num_ops_in_group]
        
        current_shift_schedule_data = {}
        for op_id in group_operators:
            op_schedule_for_this_shift = []
            for day_schedule in operator_schedules[op_id]:
                if day_schedule == shift_name or day_schedule == "DESCANSA":
                    op_schedule_for_this_shift.append(day_schedule)
                else:
                    op_schedule_for_this_shift.append("-")
            current_shift_schedule_data[op_id] = op_schedule_for_this_shift
            
        df_shift = pd.DataFrame(current_shift_schedule_data, index=[f"Semana {w+1} | {day}" for w in range(4) for day in day_names]).T
        
        st.subheader(f"Programación para {shift_name} | Operadores: {num_ops_in_group}")
        st.dataframe(df_shift)
        all_schedules_data[shift_name] = df_shift
        
        op_start_index += num_ops_in_group

    # 4. Descargar la programación
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
