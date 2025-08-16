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
# Lógica CORREGIDA de programación de turnos
# ---

st.write("---")
st.header("3. Programación de Turnos (4 Semanas)")

if st.button("Generar Programación de Turnos", key='generate_schedule_btn'):
    
    # Crear lista de todos los operadores
    all_operators = []
    for i in range(personas_actuales):
        all_operators.append(f"OP-{i + 1}")
    
    deficit = personal_total_requerido - personas_actuales
    if deficit > 0:
        for i in range(deficit):
            all_operators.append(f"OP-AD-{i + 1}")
    
    total_operators = len(all_operators)
    
    # Validar que tenemos suficientes operadores
    if total_operators < min_operadores_turno * n_turnos_dia:
        st.error(f"No hay suficientes operadores para cubrir todos los turnos. Se necesitan al menos {min_operadores_turno * n_turnos_dia} operadores.")
        st.stop()
    
    # Crear matriz de programación: [operador][dia_absoluto] = turno_asignado
    # Día absoluto: 0-27 (4 semanas * 7 días)
    total_days = 4 * 7  # 28 días
    schedule_matrix = {}
    
    # Inicializar matriz
    for operator in all_operators:
        schedule_matrix[operator] = ["DESCANSA"] * total_days
    
    # Calcular días de trabajo por operador según horas por turno
    if horas_por_turno == 12:
        # Para turnos de 12h: alternar 4 y 3 días por semana
        work_patterns = [[4, 3, 4, 3], [3, 4, 3, 4]]  # Dos patrones alternados
    elif horas_por_turno == 8:
        # Para turnos de 8h: aproximadamente 5-6 días por semana
        work_patterns = [[5, 6, 5, 6], [6, 5, 6, 5]]
    else:  # 6 horas
        # Para turnos de 6h: 6-7 días por semana
        work_patterns = [[6, 7, 6, 7], [7, 6, 7, 6]]
    
    # Asignar operadores a turnos de manera equitativa
    operators_per_shift = total_operators // n_turnos_dia
    extra_operators = total_operators % n_turnos_dia
    
    shift_operators = []
    operator_index = 0
    
    for shift in range(n_turnos_dia):
        shift_size = operators_per_shift + (1 if shift < extra_operators else 0)
        shift_ops = all_operators[operator_index:operator_index + shift_size]
        shift_operators.append(shift_ops)
        operator_index += shift_size
    
    # Programar cada operador con rotación OBLIGATORIA de turnos
    for shift_idx, shift_ops in enumerate(shift_operators):
        for op_idx, operator in enumerate(shift_ops):
            # Seleccionar patrón de trabajo
            pattern_idx = op_idx % len(work_patterns)
            work_pattern = work_patterns[pattern_idx]
            
            # Turno base del operador - DEBE cambiar cada semana
            base_shift = shift_idx
            
            for week in range(4):
                week_start = week * 7
                days_to_work = work_pattern[week]
                
                # TURNO OBLIGATORIO DIFERENTE CADA SEMANA
                current_shift = (base_shift + week) % n_turnos_dia
                shift_name = f"Turno {current_shift + 1}"
                
                # Para rotación correcta: si cambia de turno, debe haber descanso
                needs_rest_before_change = False
                rest_day_position = -1
                
                if week > 0:
                    prev_shift = (base_shift + week - 1) % n_turnos_dia
                    if prev_shift != current_shift:  # Cambia de turno
                        # Verificar si trabajó el domingo anterior
                        sunday_before = week_start - 1
                        prev_shift_name = f"Turno {prev_shift + 1}"
                        
                        if schedule_matrix[operator][sunday_before] == prev_shift_name:
                            # Trabajó el domingo, debe descansar el lunes
                            needs_rest_before_change = True
                            rest_day_position = 0  # Lunes
                        else:
                            # Ya descansó el domingo, puede trabajar desde el lunes
                            needs_rest_before_change = False
                
                # Programar la semana
                days_programmed = 0
                
                # Primero, manejar el descanso obligatorio por cambio de turno
                if needs_rest_before_change:
                    schedule_matrix[operator][week_start + rest_day_position] = "DESCANSA"
                    days_to_work = min(days_to_work, 6)  # Máximo 6 días si descansa 1
                
                # Luego, programar los días de trabajo
                work_days_count = 0
                for day_in_week in range(7):
                    absolute_day = week_start + day_in_week
                    
                    # Si es el día de descanso obligatorio, saltarlo
                    if needs_rest_before_change and day_in_week == rest_day_position:
                        continue
                    
                    # Si ya tenemos suficientes días de trabajo, el resto son descansos
                    if work_days_count >= days_to_work:
                        schedule_matrix[operator][absolute_day] = "DESCANSA"
                    else:
                        # Programar trabajo, pero distribuir algunos descansos
                        # Usar un patrón para distribuir descansos de forma variada
                        offset_pattern = (op_idx + week + day_in_week) % 7
                        total_rest_needed = 7 - days_to_work - (1 if needs_rest_before_change else 0)
                        
                        if total_rest_needed > 0 and offset_pattern < total_rest_needed and work_days_count < days_to_work:
                            # Este día será descanso para distribuir uniformemente
                            schedule_matrix[operator][absolute_day] = "DESCANSA"
                        else:
                            # Este día trabajará
                            if work_days_count < days_to_work:
                                schedule_matrix[operator][absolute_day] = shift_name
                                work_days_count += 1
                            else:
                                schedule_matrix[operator][absolute_day] = "DESCANSA"
    
    # Verificar cobertura mínima por turno y día, ajustar si es necesario
    day_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    
    for day in range(total_days):
        if day % 7 >= dias_cubrir:  # Solo verificar días que se deben cubrir
            continue
            
        for shift in range(n_turnos_dia):
            shift_name = f"Turno {shift + 1}"
            operators_in_shift = sum(1 for op in all_operators if schedule_matrix[op][day] == shift_name)
            
            if operators_in_shift < min_operadores_turno:
                # Buscar operadores que descansan ese día para asignarlos
                shortage = min_operadores_turno - operators_in_shift
                available_operators = [op for op in all_operators if schedule_matrix[op][day] == "DESCANSA"]
                
                for i in range(min(shortage, len(available_operators))):
                    schedule_matrix[available_operators[i]][day] = shift_name
    
    # Convertir a formato de visualización
    display_schedule = {}
    for operator in all_operators:
        display_schedule[operator] = schedule_matrix[operator]
    
    # Crear DataFrame para mostrar
    week_day_labels = []
    for week in range(4):
        for day in range(7):
            if day < dias_cubrir:
                week_day_labels.append(f"Semana {week+1} | {day_names[day]}")
            else:
                week_day_labels.append(f"Semana {week+1} | {day_names[day]} (No cubre)")
    
    df_schedule = pd.DataFrame(display_schedule, index=week_day_labels).T
    
    st.subheader("Programación Completa de Turnos")
    st.dataframe(df_schedule)
    
    # Verificación de cobertura
    st.subheader("Verificación de Cobertura Mínima")
    coverage_data = []
    
    for day in range(total_days):
        day_name = week_day_labels[day]
        if day % 7 < dias_cubrir:  # Solo días que se deben cubrir
            for shift in range(n_turnos_dia):
                shift_name = f"Turno {shift + 1}"
                operators_count = sum(1 for op in all_operators if schedule_matrix[op][day] == shift_name)
                status = "✅ OK" if operators_count >= min_operadores_turno else f"❌ Faltan {min_operadores_turno - operators_count}"
                coverage_data.append({
                    "Día": day_name,
                    "Turno": shift_name,
                    "Operadores": operators_count,
                    "Mínimo": min_operadores_turno,
                    "Estado": status
                })
    
    coverage_df = pd.DataFrame(coverage_data)
    st.dataframe(coverage_df)
    
    # Botón de descarga
    st.subheader("Descargar Programación")
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_schedule.to_excel(writer, sheet_name='Programación Completa')
        coverage_df.to_excel(writer, sheet_name='Verificación Cobertura', index=False)
    
    output.seek(0)
    
    st.download_button(
        label="Descargar Programación Completa en Excel",
        data=output,
        file_name='programacion_turnos_corregida.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
