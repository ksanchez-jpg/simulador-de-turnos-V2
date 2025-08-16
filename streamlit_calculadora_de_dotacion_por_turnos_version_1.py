import streamlit as st
import pandas as pd
import math
import io
from collections import deque

# ---
# 1. User Inputs and Configuration
# ---

st.title("👨‍💻 Calculadora de Personal y Programador de Turnos")
st.write("Ingresa los parámetros de tu operación para calcular el personal requerido y generar los turnos.")

st.header("1. Configuración de Turnos y Personal")

col1, col2, col3 = st.columns(3)

with col1:
    shift_type = st.selectbox(
        "Tipo de Turnos:",
        ("3 turnos de 8 horas/día", "2 turnos de 12 horas/día", "4 turnos de 6 horas/día")
    )
with col2:
    max_weekly_hours = st.number_input(
        "Máx. de horas promedio a la semana por operador:", min_value=1, value=42, step=0.5)
with col3:
    required_per_shift = st.number_input(
        "Operadores requeridos por turno (por día):", min_value=1, value=15, step=1)
    
st.write("---")
st.subheader("Personal actual")

col4, col5 = st.columns(2)
with col4:
    actual_count = st.number_input(
        "Cantidad total de personal actual:", min_value=0, value=45, step=1)
with col5:
    coverage_days_per_week = st.number_input(
        "Días a laborar por semana para cobertura:", min_value=1, max_value=7, value=7, step=1)

# ---
# 2. Calculation and Results
# ---

st.header("2. Análisis de Requerimiento de Personal")

if st.button(f"Calcular y Generar Programación"):
    st.write("---")

    # --- Step 1: Define shift hours and number of shifts ---
    if shift_type == "3 turnos de 8 horas/día":
        hours_per_shift = 8
        num_shifts = 3
    elif shift_type == "2 turnos de 12 horas/día":
        hours_per_shift = 12
        num_shifts = 2
    else:  # 4 turnos de 6 horas/día
        hours_per_shift = 6
        num_shifts = 4
    
    # --- Step 2: Perform the core calculation based on total hours ---
    required_weekly_hours_total = required_per_shift * hours_per_shift * num_shifts * coverage_days_per_week
    theoretical_required_operators = required_weekly_hours_total / max_weekly_hours
    total_required = math.ceil(theoretical_required_operators)
    
    available_weekly_hours = actual_count * max_weekly_hours

    # --- Step 3: Display results ---
    st.subheader(f"Resultados del Cálculo:")
    
    st.markdown(f"**Personal requerido por turno (ingresado):** `{required_per_shift}`")
    st.markdown(f"**Cantidad de operadores requeridos (teórico):** `{total_required}`")
    st.markdown(f"**Cantidad de personal actual:** `{actual_count}`")
    st.markdown(f"**Horas semanales que se deben cubrir:** `{required_weekly_hours_total:.2f}` horas")

    if actual_count >= total_required:
        st.success(f"✅ ¡El personal actual es suficiente!")
        deficit = 0
    else:
        st.error(f"❌ El personal actual es insuficiente.")
        deficit = total_required - actual_count
        st.markdown(f"**Operadores adicionales requeridos:** `{deficit}`")
        
    st.write("---")

    # ---
    # 3. Final Step: Generate Shift Schedule
    # ---
    
    st.header("3. Programación de Turnos (4 Semanas)")
    
    # Logic for distributing operators with remainder to Turno 2
    operators_per_shift_group = [math.floor(total_required / num_shifts)] * num_shifts
    remainder = total_required % num_shifts
    if remainder > 0:
        if num_shifts >= 2:
            operators_per_shift_group[1] += remainder
        else:
            operators_per_shift_group[0] += remainder

    day_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    
    # Global counter for unique operator IDs
    operator_counter = 0
    
    # Queue for additional operators
    additional_operators = deque([f"OP-AD-{i + 1}" for i in range(deficit)])
    
    # Dictionary to hold the final schedule data for all shifts
    all_schedules_data = {}

    # Generate a schedule for EACH daily shift group
    for shift_index in range(num_shifts):
        
        shift_name = f"Turno {shift_index + 1}"
        current_shift_schedule = {}

        st.subheader(f"Programación para {shift_name} | Operadores: {operators_per_shift_group[shift_index]}")
        
        for _ in range(operators_per_shift_group[shift_index]):
            
            # Determine if the current operator is actual or additional
            if operator_counter < actual_count:
                operator_id = f"OP-{operator_counter + 1}"
            else:
                operator_id = additional_operators.popleft()

            operator_schedule = []
            sunday_count = 0
            
            # Logic for 42-hour average and varied rest days over 3 weeks
            # The pattern repeats
            
            # 8-hour shifts: 5 days work (40h), 6 days work (48h), 5 days work (40h) -> 128h over 3 weeks -> 42.6h/week
            # I will implement a pattern that can be varied
            
            # Schedule pattern: days to work per week (0-indexed)
            if hours_per_shift == 12:
                work_days_pattern = [4, 3, 4, 3] # Averages to 42h/week over 2 weeks
            elif hours_per_shift == 8:
                work_days_pattern = [5, 6, 5, 5] # Averages to 42h/week over 4 weeks (168h total)
            else: # 6-hour shifts
                work_days_pattern = [7, 7, 7, 7] # 42h/week
            
            # This offset ensures the rest days are not always the same for each operator
            stagger_offset = operator_counter % 7
            
            for week in range(4):
                days_to_work = work_days_pattern[week]
                
                # Assign shifts based on rotation
                assigned_shift = f"Turno {((week + shift_index) % num_shifts) + 1}"
                
                for day_of_week in range(7):
                    day_in_rotation = (day_of_week + stagger_offset) % 7
                    
                    if day_in_rotation < days_to_work:
                        # Check for max 2 consecutive Sundays
                        if day_of_week == 6 and sunday_count < 2:
                            operator_schedule.append(assigned_shift)
                            sunday_count += 1
                        elif day_of_week == 6 and sunday_count >= 2:
                            operator_schedule.append("DESCANSA")
                            sunday_count = 0
                        else:
                             operator_schedule.append(assigned_shift)
                    else:
                        operator_schedule.append("DESCANSA")
            
            current_shift_schedule[operator_id] = operator_schedule
            operator_counter += 1
        
        df = pd.DataFrame(current_shift_schedule, index=[f"Semana {w+1} | {day_names[d]}" for w in range(4) for d in range(7)]).T
        st.dataframe(df)

        all_schedules_data[f"Turno {shift_index + 1}"] = df

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
