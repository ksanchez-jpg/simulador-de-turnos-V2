import random
import pandas as pd
import streamlit as st

# ================================
# PARÁMETROS DEL SISTEMA
# ================================
total_operadores = 15          # Total de operadores
n_turnos_dia = 3               # Cambia aquí: 3=3x8, 2=2x12, 4=4x6
horas_por_turno = {3: 8, 2: 12, 4: 6}[n_turnos_dia]
dias_cubrir = 5                # Días de cobertura por semana (ej: 5)
min_operadores_turno = 2       # Mínimo de operadores por turno
total_semanas = 4              # Semanas de planificación
total_days = total_semanas * 7 # Días totales

# ================================
# CREACIÓN DE OPERADORES
# ================================
all_operators = [f"Operador {i+1}" for i in range(total_operadores)]

# ================================
# PROGRAMACIÓN DE TURNOS
# ================================
schedule_matrix = {op: [""] * total_days for op in all_operators}

for week in range(total_semanas):
    available_ops = all_operators.copy()
    random.shuffle(available_ops)

    # Dividir en grupos por turnos
    groups = [available_ops[i::n_turnos_dia] for i in range(n_turnos_dia)]

    for day in range(7):
        if day >= dias_cubrir:  # Días no cubiertos
            for op in all_operators:
                schedule_matrix[op][week*7 + day] = "DESCANSO"
            continue

        for shift, group in enumerate(groups):
            shift_name = f"Turno {shift + 1}"
            for op in group:
                schedule_matrix[op][week*7 + day] = shift_name

# ================================
# CREAR DATAFRAME DE PROGRAMACIÓN
# ================================
week_day_labels = [f"Semana {d//7 + 1} - Día {d%7 + 1}" for d in range(total_days)]
df_schedule = pd.DataFrame(schedule_matrix, index=week_day_labels).T

# ================================
# TABLA DE COBERTURA
# ================================
coverage_data = []

for day in range(total_days):
    if day % 7 >= dias_cubrir:
        continue

    for shift in range(n_turnos_dia):  # ✅ Dinámico según modalidad
        shift_name = f"Turno {shift + 1}"
        operators_count = sum(1 for op in all_operators if schedule_matrix[op][day] == shift_name)
        status = "✅ OK" if operators_count >= min_operadores_turno else f"❌ Faltan {min_operadores_turno - operators_count}"
        coverage_data.append({
            "Día": week_day_labels[day],
            "Turno": shift_name,
            "Operadores": operators_count,
            "Mínimo": min_operadores_turno,
            "Estado": status
        })

df_coverage = pd.DataFrame(coverage_data)

# ================================
# MOSTRAR RESULTADOS
# ================================
print("=== Programación de Turnos ===")
print(df_schedule)

print("\n=== Verificación de Cobertura ===")
print(df_coverage)
