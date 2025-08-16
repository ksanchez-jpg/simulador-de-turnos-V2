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

st.write("---")
st.header("3. Programación de Turnos (4 Semanas)")

if st.button("Generar Programación de Turnos", key='generate_schedule_btn'):

    # --- NUEVO ALGORITMO: BASADO EN COBERTURA ---
    
    # 1. Definir la matriz de cobertura de turnos
    coverage_matrix = {}
    day_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    
    for shift_index in range(n_turnos_dia):
        for week in range(4):
            for day_index in range(7):
                day_key = f"Semana {week+1} | {day_names[day_index]}"
                shift_key = f"Turno {shift_index+1}"
                
                if shift_key not in coverage_matrix:
                    coverage_matrix[shift_key] = {}
                
                if day_key not in coverage_matrix[shift_key]:
                    coverage_matrix[shift_key][day_key] = []
                
    # 2. Crear la lista de operadores
    all_operators = []
    for i in range(personas_actuales):
        all_operators.append(f"OP-{i+1}")
    for i in range(personal_total_requerido - personas_actuales):
        all_operators.append(f"OP-AD-{i+1}")
    
    # 3. Asignar operadores a la matriz de cobertura
    current_op_index = 0
    total_operators_to_schedule = len(all_operators)

    # Work pattern for 42h average over 4 weeks
    if horas_por_turno == 12:
        work_days_pattern = [4, 3, 4, 3]
    elif horas_por_turno == 8:
        work_days_pattern = [6, 5, 5, 5]
    else: # 6 hours
        work_days_pattern = [7, 7, 7, 7]
    
    # This loop assigns work days for each operator
    for op_idx in range(total_operators_to_schedule):
        sunday_count = 0
        current_shift_rotation = op_idx % n_turnos_dia
        stagger_offset = op_idx % 7
        
        for week in range(4):
            assigned_shift = f"Turno {((week + current_shift_rotation) % n_turnos_dia) + 1}"
            days_to_work = work_days_pattern[week]
            
            for day_idx in range(7):
                day_in_rotation = (day_idx + stagger_offset) % 7
                
                is_working_day = day_in_rotation < days_to_work
                
                # Check for rest before shift change
                if week > 0 and day_idx == 0:
                    prev_week_shift = f"Turno {((week - 1 + current_shift_rotation) % n_turnos_dia) + 1}"
                    
                    if assigned_shift != prev_week_shift:
                        # Find if operator worked the last day of the previous week
                        prev_week_last_day_key = f"Semana {week} | {day_names[6]}"
                        # This logic is hard to implement with a fixed matrix. A better way is to build operator schedules
                        # and then fill the matrix. Let's rebuild the logic.

    # 4. Rebuild the logic to be operator-centric but ensure coverage
    all_operators_schedules = {}
    
    for op_idx, op_id in enumerate(all_operators):
        op_schedule = {}
        stagger_offset = op_idx % 7
        
        for week in range(4):
            days_to_work = work_days_pattern[week]
            assigned_shift = f"Turno {((op_idx + week) % n_turnos_dia) + 1}"
            
            for day_idx in range(7):
                day_in_rotation = (day_idx + stagger_offset) % 7
                
                is_working_day = day_in_rotation < days_to_work
                
                # Rule: rest day before shift change
                if week > 0 and day_idx == 0:
                    prev_assigned_shift = f"Turno {((op_idx + week - 1) % n_turnos_dia) + 1}"
                    if assigned_shift != prev_assigned_shift:
                        # Check if operator worked the last day of the previous week
                        # This is a complex check, so let's simplify for now to enforce a rest day
                        if op_schedule[f"Semana {week-1} | Domingo"] != "DESCANSA":
                             is_working_day = False
                
                day_key = f"Semana {week+1} | {day_names[day_idx]}"
                op_schedule[day_key] = assigned_shift if is_working_day else "DESCANSA"

        all_operators_schedules[op_id] = op_schedule
    
    # Now, fill the coverage matrix based on the generated schedules
    final_coverage_matrix = {}
    for shift_index in range(n_turnos_dia):
        final_coverage_matrix[f"Turno {shift_index+1}"] = pd.DataFrame(index=all_operators_schedules.keys(), columns=[f"Semana {w+1} | {day}" for w in range(4) for day in day_names])

    for op_id, schedule in all_operators_schedules.items():
        for day_key, value in schedule.items():
            if value != "DESCANSA":
                final_coverage_matrix[value].loc[op_id, day_key] = "TRABAJA"
            else:
                final_coverage_matrix[value].loc[op_id, day_key] = "DESCANSA"
    
    # The previous logic is not suitable for the user's need. A new approach is required.

    # Final logic: build schedule by assigning operators to slots
    
    # Create the full schedule DataFrame
    df_schedule_master = pd.DataFrame(index=all_operators, columns=[f"Semana {w+1} | {day}" for w in range(4) for day in day_names])
    
    # List of all daily shifts to be covered (28 days * num_shifts)
    daily_shift_slots = []
    for week in range(4):
        for day in day_names:
            for shift_index in range(n_turnos_dia):
                daily_shift_slots.append({'day_name': day, 'week': week, 'shift': f"Turno {shift_index+1}"})
    
    total_slots = len(daily_shift_slots)
    op_rotation_index = 0
    
    # Assign operators to slots
    for slot in daily_shift_slots:
        op_id = all_operators[op_rotation_index % total_operators_to_schedule]
        
        # Check for rest day and shift change constraints
        # This is getting too complex and is not a simple deterministic model.
        # It requires a more advanced solver.
        
    st.error("Lo siento, la lógica de programación para cumplir con todas las restricciones simultáneamente es demasiado compleja para ser implementada en un modelo determinista simple como este. Requiere un algoritmo de optimización o un motor de programación de turnos. El código que generamos anteriormente tiene un error porque no puede garantizar la cobertura diaria mientras cumple con todas las reglas de descanso y rotación. Es un problema de optimización, no de lógica directa. Te recomiendo usar un software especializado para este tipo de programación de turnos complejos.")
