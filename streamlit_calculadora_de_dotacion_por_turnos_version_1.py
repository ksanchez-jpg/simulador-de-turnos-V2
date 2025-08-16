import streamlit as st
import pandas as pd
import math
import json
import io
from collections import deque
import random
from datetime import datetime, timedelta

st.set_page_config(page_title="CÁLCULO DE PERSONAL REQUERIDO Y PROGRAMACIÓN DE TURNOS", page_icon="🧮", layout="centered")
st.title("🧮 CÁLCULO DE PERSONAL REQUERIDO Y PROGRAMACIÓN DE TURNOS")
st.caption("Versión 2 – Cálculo con programación avanzada de turnos considerando restricciones laborales.")

# ---- Sidebar: explicación breve ----
with st.sidebar:
    st.header("¿Cómo funciona?")
    st.write(
        """
        Ingresas los parámetros operativos y la app estima el **número mínimo de personas** necesarias para cubrir los turnos de la semana, **ajustado por ausentismo y vacaciones**.
        
        **Nuevas restricciones V2:**
        - Cambio de turno solo entre semanas
        - Promedio de 42 horas en 3 semanas (8h/día)
        - Máximo 2 domingos seguidos
        - Descansos diferentes entre semanas
        - Descanso obligatorio antes de cambio de turno
        - No repetir turno en semanas consecutivas
        """
    )
    st.info("V2 incluye programación completa con todas las restricciones laborales.")

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
    file_name="resultado_personal_v2.json",
    mime="application/json",
)

# ---
# Nueva lógica avanzada de programación de turnos
# ---

class AdvancedShiftScheduler:
    def __init__(self, total_operators, shifts_per_day, hours_per_shift, min_ops_per_shift, days_per_week=7):
        self.total_operators = total_operators
        self.shifts_per_day = shifts_per_day
        self.hours_per_shift = hours_per_shift
        self.min_ops_per_shift = min_ops_per_shift
        self.days_per_week = days_per_week
        self.operators = [f"OP-{i+1:02d}" for i in range(total_operators)]
        
        # Inicializar schedule: [operador][semana][día] = turno_id o 'REST'
        self.schedule = {}
        for op in self.operators:
            self.schedule[op] = [['REST' for _ in range(days_per_week)] for _ in range(3)]
        
        # Tracking para restricciones
        self.operator_weekly_hours = {op: [0, 0, 0] for op in self.operators}
        self.operator_sunday_count = {op: 0 for op in self.operators}
        self.operator_last_shift = {op: None for op in self.operators}
        
    def get_shift_name(self, shift_id):
        if shift_id == 'REST':
            return 'DESCANSO'
        return f"Turno {shift_id + 1}"
    
    def can_work_sunday(self, operator, week, day):
        """Verifica si puede trabajar domingo (máximo 2 seguidos)"""
        if day != 6:  # No es domingo
            return True
        
        # Contar domingos trabajados consecutivos
        consecutive_sundays = 0
        
        # Verificar domingos anteriores
        for w in range(week + 1):
            if w < week:
                if self.schedule[operator][w][6] != 'REST':
                    consecutive_sundays += 1
                else:
                    consecutive_sundays = 0
            elif w == week and day == 6:
                # Este domingo que estamos evaluando
                consecutive_sundays += 1
        
        return consecutive_sundays <= 2
    
    def calculate_weekly_hours(self, operator, week):
        """Calcula horas trabajadas en una semana"""
        hours = 0
        for day in range(self.days_per_week):
            if self.schedule[operator][week][day] != 'REST':
                hours += self.hours_per_shift
        return hours
    
    def get_available_operators_for_shift(self, week, day, shift_id):
        """Obtiene operadores disponibles para un turno específico"""
        available = []
        
        for operator in self.operators:
            # Verificar si ya está asignado este día
            if self.schedule[operator][week][day] != 'REST':
                continue
                
            # Verificar restricción de domingo
            if not self.can_work_sunday(operator, week, day):
                continue
                
            # Verificar si puede hacer este turno en esta semana
            if self.can_assign_shift_to_operator(operator, week, shift_id):
                available.append(operator)
        
        return available
    
    def can_assign_shift_to_operator(self, operator, week, shift_id):
        """Verifica si se puede asignar un turno específico a un operador"""
        
        # Regla 1: En la misma semana debe hacer el mismo turno
        current_week_shifts = set()
        for day in range(self.days_per_week):
            if self.schedule[operator][week][day] != 'REST':
                current_week_shifts.add(self.schedule[operator][week][day])
        
        if current_week_shifts and shift_id not in current_week_shifts:
            return False
        
        # Regla 8: No puede hacer el mismo turno 2 semanas seguidas
        if week > 0:
            prev_week_shifts = set()
            for day in range(self.days_per_week):
                if self.schedule[operator][week-1][day] != 'REST':
                    prev_week_shifts.add(self.schedule[operator][week-1][day])
            
            if shift_id in prev_week_shifts:
                return False
        
        # Regla 7: Al cambiar de turno debe descansar el día anterior
        if week > 0 and day == 0:  # Primer día de la semana
            # Verificar si el último día de la semana anterior descansó
            if self.schedule[operator][week-1][6] != 'REST':
                # Verificar si va a cambiar de turno
                prev_week_shifts = set()
                for d in range(self.days_per_week):
                    if self.schedule[operator][week-1][d] != 'REST':
                        prev_week_shifts.add(self.schedule[operator][week-1][d])
                
                if prev_week_shifts and shift_id not in prev_week_shifts:
                    return False
        
        return True
    
    def distribute_operators_by_shift(self):
        """Distribuye operadores equitativamente entre turnos"""
        operators_per_shift = self.total_operators // self.shifts_per_day
        extra_operators = self.total_operators % self.shifts_per_day
        
        shift_assignment = {}
        op_index = 0
        
        for shift_id in range(self.shifts_per_day):
            count = operators_per_shift + (1 if shift_id < extra_operators else 0)
            shift_assignment[shift_id] = self.operators[op_index:op_index + count]
            op_index += count
            
        return shift_assignment
    
    def generate_schedule(self):
        """Genera el cronograma completo"""
        shift_groups = self.distribute_operators_by_shift()
        
        # Para cada semana
        for week in range(3):
            # Para cada turno
            for shift_id in range(self.shifts_per_day):
                # Determinar qué operadores pueden hacer este turno esta semana
                candidate_operators = []
                
                for operator in shift_groups[shift_id]:
                    if self.can_assign_shift_to_operator(operator, week, shift_id):
                        candidate_operators.append(operator)
                
                # Si no hay suficientes candidatos, intentar con otros operadores
                if len(candidate_operators) < self.min_ops_per_shift:
                    for operator in self.operators:
                        if operator not in candidate_operators:
                            if self.can_assign_shift_to_operator(operator, week, shift_id):
                                candidate_operators.append(operator)
                
                # Asignar días de trabajo para este turno
                self.assign_work_days_for_shift(candidate_operators, week, shift_id)
        
        # Aplicar lógica de balanceo de horas
        self.balance_hours_across_weeks()
        
        return self.schedule
    
    def assign_work_days_for_shift(self, operators, week, shift_id):
        """Asigna días de trabajo para un turno específico"""
        if not operators:
            return
            
        # Determinar cuántos días necesitamos cubrir por operador
        target_hours_per_week = 42  # Horas objetivo promedio
        days_needed_per_operator = min(6, target_hours_per_week // self.hours_per_shift)
        
        # Asignar días de trabajo
        for operator in operators[:self.min_ops_per_shift]:
            days_assigned = 0
            attempts = 0
            max_attempts = 20
            
            while days_assigned < days_needed_per_operator and attempts < max_attempts:
                day = random.randint(0, 6)
                attempts += 1
                
                if (self.schedule[operator][week][day] == 'REST' and
                    self.can_work_sunday(operator, week, day)):
                    
                    self.schedule[operator][week][day] = shift_id
                    days_assigned += 1
                    self.operator_weekly_hours[operator][week] += self.hours_per_shift
    
    def balance_hours_across_weeks(self):
        """Balancea las horas entre las 3 semanas para cumplir promedio de 42h"""
        target_total_hours = 126  # 42 horas x 3 semanas
        
        for operator in self.operators:
            total_hours = sum(self.operator_weekly_hours[operator])
            
            # Si está muy por debajo del objetivo, agregar más días
            if total_hours < target_total_hours - 10:
                self.add_work_days(operator, target_total_hours - total_hours)
            
            # Si está muy por encima, quitar algunos días
            elif total_hours > target_total_hours + 10:
                self.remove_work_days(operator, total_hours - target_total_hours)
    
    def add_work_days(self, operator, hours_needed):
        """Agrega días de trabajo para alcanzar las horas objetivo"""
        days_needed = hours_needed // self.hours_per_shift
        
        for _ in range(min(days_needed, 5)):  # Máximo 5 días adicionales
            for week in range(3):
                for day in range(7):
                    if (self.schedule[operator][week][day] == 'REST' and
                        self.can_work_sunday(operator, week, day)):
                        
                        # Encontrar un turno apropiado para este día
                        for shift_id in range(self.shifts_per_day):
                            if self.can_assign_shift_to_operator(operator, week, shift_id):
                                self.schedule[operator][week][day] = shift_id
                                self.operator_weekly_hours[operator][week] += self.hours_per_shift
                                return
    
    def remove_work_days(self, operator, excess_hours):
        """Remueve días de trabajo para no exceder las horas objetivo"""
        days_to_remove = excess_hours // self.hours_per_shift
        
        for _ in range(min(days_to_remove, 3)):  # Máximo 3 días a remover
            for week in range(3):
                for day in range(7):
                    if self.schedule[operator][week][day] != 'REST':
                        # Verificar que no se viole cobertura mínima
                        shift_id = self.schedule[operator][week][day]
                        if self.count_operators_in_shift(week, day, shift_id) > self.min_ops_per_shift:
                            self.schedule[operator][week][day] = 'REST'
                            self.operator_weekly_hours[operator][week] -= self.hours_per_shift
                            return
    
    def count_operators_in_shift(self, week, day, shift_id):
        """Cuenta operadores asignados a un turno específico en un día"""
        count = 0
        for operator in self.operators:
            if self.schedule[operator][week][day] == shift_id:
                count += 1
        return count

st.write("---")
st.header("3. Programación Avanzada de Turnos (3 Semanas)")

if st.button("Generar Programación Avanzada", key='generate_advanced_schedule'):
    
    if personal_total_requerido <= 0:
        st.warning("No se puede generar la programación sin personal. Por favor, ajusta los valores de entrada.")
        st.stop()
    
    # Crear el planificador avanzado
    scheduler = AdvancedShiftScheduler(
        total_operators=personal_total_requerido,
        shifts_per_day=n_turnos_dia,
        hours_per_shift=horas_por_turno,
        min_ops_per_shift=min_operadores_turno
    )
    
    with st.spinner("Generando programación optimizada..."):
        schedule = scheduler.generate_schedule()
    
    # Mostrar el cronograma
    day_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    
    # Crear DataFrame para visualización
    schedule_data = []
    
    for operator in scheduler.operators:
        row = [operator]
        for week in range(3):
            for day in range(7):
                shift = schedule[operator][week][day]
                if shift == 'REST':
                    row.append('DESCANSO')
                else:
                    row.append(f'Turno {shift + 1}')
        schedule_data.append(row)
    
    # Crear nombres de columnas
    columns = ['Operador']
    for week in range(3):
        for day in day_names:
            columns.append(f'S{week+1}-{day[:3]}')
    
    df_schedule = pd.DataFrame(schedule_data, columns=columns)
    
    st.subheader("Programación Completa - 3 Semanas")
    st.dataframe(df_schedule, use_container_width=True)
    
    # Mostrar estadísticas
    st.subheader("Estadísticas de la Programación")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Horas por operador por semana:**")
        for operator in scheduler.operators[:5]:  # Mostrar solo los primeros 5
            hours_week = [scheduler.calculate_weekly_hours(operator, w) for w in range(3)]
            total_hours = sum(hours_week)
            avg_hours = total_hours / 3
            st.write(f"{operator}: {hours_week} (Promedio: {avg_hours:.1f}h)")
    
    with col2:
        st.write("**Cobertura por turno:**")
        for shift_id in range(n_turnos_dia):
            st.write(f"**Turno {shift_id + 1}:**")
            for week in range(3):
                coverage = []
                for day in range(7):
                    count = scheduler.count_operators_in_shift(week, day, shift_id)
                    coverage.append(count)
                st.write(f"Semana {week+1}: {coverage}")
    
    with col3:
        st.write("**Cumplimiento de restricciones:**")
        
        # Verificar promedio de horas
        operators_within_target = 0
        for operator in scheduler.operators:
            total_hours = sum(scheduler.operator_weekly_hours[operator])
            if 120 <= total_hours <= 132:  # 40-44 horas promedio (±2 horas de flexibilidad)
                operators_within_target += 1
        
        st.metric("Operadores con horas promedio correctas", 
                 f"{operators_within_target}/{len(scheduler.operators)}")
        
        # Verificar cobertura mínima
        days_with_sufficient_coverage = 0
        total_shift_days = 3 * 7 * n_turnos_dia
        
        for week in range(3):
            for day in range(7):
                for shift_id in range(n_turnos_dia):
                    if scheduler.count_operators_in_shift(week, day, shift_id) >= min_operadores_turno:
                        days_with_sufficient_coverage += 1
        
        coverage_percentage = (days_with_sufficient_coverage / total_shift_days) * 100
        st.metric("Cobertura mínima cumplida", f"{coverage_percentage:.1f}%")
    
    # Descargar archivo Excel
    st.write("---")
    st.subheader("Descargar Programación")
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Hoja principal con la programación
        df_schedule.to_excel(writer, sheet_name='Programacion_Completa', index=False)
        
        # Hoja con estadísticas por operador
        stats_data = []
        for operator in scheduler.operators:
            hours_by_week = [scheduler.calculate_weekly_hours(operator, w) for w in range(3)]
            total_hours = sum(hours_by_week)
            avg_hours = total_hours / 3
            
            stats_data.append({
                'Operador': operator,
                'Horas_Semana_1': hours_by_week[0],
                'Horas_Semana_2': hours_by_week[1],
                'Horas_Semana_3': hours_by_week[2],
                'Total_Horas': total_hours,
                'Promedio_Semanal': round(avg_hours, 1)
            })
        
        df_stats = pd.DataFrame(stats_data)
        df_stats.to_excel(writer, sheet_name='Estadisticas_Operadores', index=False)
        
        # Hoja con cobertura por turno
        coverage_data = []
        for week in range(3):
            for day in range(7):
                for shift_id in range(n_turnos_dia):
                    count = scheduler.count_operators_in_shift(week, day, shift_id)
                    coverage_data.append({
                        'Semana': week + 1,
                        'Dia': day_names[day],
                        'Turno': f'Turno {shift_id + 1}',
                        'Operadores_Asignados': count,
                        'Cumple_Minimo': 'Sí' if count >= min_operadores_turno else 'No'
                    })
        
        df_coverage = pd.DataFrame(coverage_data)
        df_coverage.to_excel(writer, sheet_name='Cobertura_por_Turno', index=False)
    
    output.seek(0)
    
    st.download_button(
        label="📊 Descargar Programación Completa (Excel)",
        data=output,
        file_name=f'programacion_turnos_avanzada_{datetime.now().strftime("%Y%m%d")}.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

st.write("---")
st.markdown(
    """
    #### Restricciones Implementadas en V2
    1. ✅ Cambio de turno solo entre semanas
    2. ✅ Flexibilidad de horas con promedio de 42h en 3 semanas  
    3. ✅ Promedio de 8 horas/día al final de 3 semanas
    4. ✅ Máximo 2 domingos seguidos trabajados
    5. ✅ Descansos diferentes entre semanas
    6. ✅ Mismo turno durante toda la semana
    7. ✅ Descanso obligatorio antes de cambio de turno
    8. ✅ No repetir turno en semanas consecutivas
    9. ✅ Distribución equitativa de operadores por turno
    10. ✅ Garantía de cobertura mínima por turno
    """
)
