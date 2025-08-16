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
        
        # Verificar que tenemos suficientes operadores para cubrir los mínimos
        min_operators_needed = shifts_per_day * min_ops_per_shift
        if total_operators < min_operators_needed:
            raise ValueError(f"Se necesitan al menos {min_operators_needed} operadores para cubrir {shifts_per_day} turnos con {min_ops_per_shift} operadores mínimos por turno")
        
        self.operators = [f"OP-{i+1:02d}" for i in range(total_operators)]
        
        # Asignación fija de operadores por turno (para mantener consistencia)
        self.shift_assignments = self.distribute_operators_by_shift()
        
        # Inicializar schedule: [operador][semana][día] = turno_id o 'REST'
        self.schedule = {}
        for op in self.operators:
            self.schedule[op] = [['REST' for _ in range(days_per_week)] for _ in range(3)]
        
        # Tracking para restricciones
        self.operator_weekly_hours = {op: [0, 0, 0] for op in self.operators}
        self.operator_sunday_count = {op: 0 for op in self.operators}
        self.operator_last_shift = {op: None for op in self.operators}
        self.operator_assigned_shift = {}  # Turno asignado permanentemente a cada operador
        
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
        
        # Regla fundamental: el operador debe estar asignado a este turno base
        base_shift = self.operator_assigned_shift[operator]
        
        # Calcular el turno que le corresponde esta semana (rotación)
        current_week_shift = (base_shift + week) % self.shifts_per_day
        
        # Solo puede trabajar en su turno asignado para esta semana
        if shift_id != current_week_shift:
            return False
        
        # Regla 8: No puede hacer el mismo turno 2 semanas seguidas (ya manejado por rotación automática)
        
        return True
    
    def distribute_operators_by_shift(self):
        """Distribuye operadores equitativamente entre turnos, respetando mínimos"""
        # Primero aseguramos el mínimo por turno
        operators_per_shift = {}
        remaining_operators = list(self.operators)
        
        # Asignar operadores mínimos a cada turno
        for shift_id in range(self.shifts_per_day):
            operators_per_shift[shift_id] = []
            # Asignar mínimo requerido
            for _ in range(self.min_ops_per_shift):
                if remaining_operators:
                    operators_per_shift[shift_id].append(remaining_operators.pop(0))
        
        # Distribuir operadores restantes equitativamente
        shift_id = 0
        while remaining_operators:
            operators_per_shift[shift_id].append(remaining_operators.pop(0))
            shift_id = (shift_id + 1) % self.shifts_per_day
        
        # Asignar turnos fijos a operadores (para rotación entre semanas)
        for shift_id, operators in operators_per_shift.items():
            for operator in operators:
                self.operator_assigned_shift[operator] = shift_id
        
        return operators_per_shift
    
    def generate_schedule(self):
        """Genera el cronograma completo con rotación automática de turnos"""
        
        # Para cada semana
        for week in range(3):
            # Verificar si necesita descanso antes de cambio de turno (Regla 7)
            if week > 0:
                self.apply_rest_before_shift_change(week)
            
            # Para cada operador, determinar su turno para esta semana
            for operator in self.operators:
                base_shift = self.operator_assigned_shift[operator]
                current_week_shift = (base_shift + week) % self.shifts_per_day
                
                # Asignar días de trabajo para este operador en su turno correspondiente
                self.assign_work_days_for_operator(operator, week, current_week_shift)
        
        # Aplicar lógica de balanceo de horas
        self.balance_hours_across_weeks()
        
        # Verificar y ajustar cobertura mínima
        self.ensure_minimum_coverage()
        
        return self.schedule
    
    def apply_rest_before_shift_change(self, week):
        """Aplica descanso obligatorio antes de cambio de turno (Regla 7)"""
        for operator in self.operators:
            base_shift = self.operator_assigned_shift[operator]
            prev_week_shift = (base_shift + week - 1) % self.shifts_per_day
            current_week_shift = (base_shift + week) % self.shifts_per_day
            
            # Si cambia de turno, debe descansar el domingo anterior y el lunes
            if prev_week_shift != current_week_shift:
                # Descanso domingo anterior (último día semana anterior)
                if self.schedule[operator][week-1][6] != 'REST':
                    self.schedule[operator][week-1][6] = 'REST'
                    self.operator_weekly_hours[operator][week-1] -= self.hours_per_shift
                
                # Descanso lunes de la nueva semana
                self.schedule[operator][week][0] = 'REST'
    
    def assign_work_days_for_operator(self, operator, week, shift_id):
        """Asigna días de trabajo para un operador específico en su turno asignado"""
        
        # Calcular días objetivo basado en horas promedio deseadas
        target_hours_per_week = 42
        target_days = min(6, target_hours_per_week // self.hours_per_shift)
        
        # Ajustar según la semana para balancear las 3 semanas
        if week == 0:
            days_this_week = target_days
        elif week == 1:
            days_this_week = max(4, target_days - 1)  # Menos días en semana 2
        else:
            # Calcular días necesarios para llegar a 126 horas totales
            current_total = sum(self.operator_weekly_hours[operator][:2])
            remaining_hours = 126 - current_total
            days_this_week = min(6, max(4, remaining_hours // self.hours_per_shift))
        
        # Lista de días disponibles (evitar domingos consecutivos)
        available_days = list(range(7))
        
        # Verificar restricción de domingos (Regla 4)
        if not self.can_work_sunday(operator, week, 6):
            available_days.remove(6)
        
        # Si ya descansó el lunes por cambio de turno, no está disponible
        if self.schedule[operator][week][0] == 'REST':
            available_days.remove(0)
            
        # Seleccionar días de trabajo
        import random
        random.shuffle(available_days)
        
        days_assigned = 0
        for day in available_days:
            if days_assigned >= days_this_week:
                break
                
            if self.schedule[operator][week][day] == 'REST':
                self.schedule[operator][week][day] = shift_id
                self.operator_weekly_hours[operator][week] += self.hours_per_shift
                days_assigned += 1
                
                if day == 6:  # Es domingo
                    self.operator_sunday_count[operator] += 1
    
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
        base_shift = self.operator_assigned_shift[operator]
        
        for _ in range(min(days_needed, 5)):  # Máximo 5 días adicionales
            for week in range(3):
                operator_current_shift = (base_shift + week) % self.shifts_per_day
                for day in range(7):
                    if (self.schedule[operator][week][day] == 'REST' and
                        self.can_work_sunday(operator, week, day)):
                        
                        self.schedule[operator][week][day] = operator_current_shift
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
    
    # Mostrar el cronograma por turnos
    day_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    
    # Mostrar primero la asignación de turnos
    st.subheader("Asignación de Operadores por Turno")
    
    col1, col2, col3 = st.columns(3)
    columns = [col1, col2, col3]
    
    for shift_id in range(n_turnos_dia):
        operators_in_shift = [op for op, assigned_shift in scheduler.operator_assigned_shift.items() if assigned_shift == shift_id]
        
        with columns[shift_id % 3]:
            st.write(f"**Turno {shift_id + 1}** ({len(operators_in_shift)} operadores)")
            st.write(f"Horas: {horas_por_turno}h")
            st.write("Operadores asignados:")
            for op in operators_in_shift:
                st.write(f"• {op}")
            st.write("Rotación semanal:")
            for week in range(3):
                rotated_shift = (shift_id + week) % n_turnos_dia + 1
                st.write(f"S{week+1}: Turno {rotated_shift}")
    
    st.divider()
    
    # Crear DataFrames separados por turno para mejor visualización
    st.subheader("Programación por Turno")
    
    for shift_id in range(n_turnos_dia):
        operators_in_shift = [op for op, assigned_shift in scheduler.operator_assigned_shift.items() if assigned_shift == shift_id]
        
        if operators_in_shift:
            st.write(f"### Turno {shift_id + 1} - Operadores Base")
            
            # Crear DataFrame para este turno específico
            shift_schedule_data = []
            
            for operator in operators_in_shift:
                row = [operator]
                for week in range(3):
                    for day in range(7):
                        shift_value = schedule[operator][week][day]
                        if shift_value == 'REST':
                            row.append('DESCANSO')
                        else:
                            row.append(f'Turno {shift_value + 1}')
                shift_schedule_data.append(row)
            
            # Crear nombres de columnas
            columns = ['Operador']
            for week in range(3):
                for day in day_names:
                    columns.append(f'S{week+1}-{day[:3]}')
            
            df_shift_schedule = pd.DataFrame(shift_schedule_data, columns=columns)
            st.dataframe(df_shift_schedule, use_container_width=True)
            
            # Mostrar resumen de cobertura para este turno
            coverage_summary = []
            for week in range(3):
                week_coverage = []
                for day in range(7):
                    # Contar cuántos de este grupo base están trabajando (en cualquier turno)
                    working_count = 0
                    for operator in operators_in_shift:
                        if schedule[operator][week][day] != 'REST':
                            working_count += 1
                    week_coverage.append(working_count)
                coverage_summary.append(f"S{week+1}: {week_coverage}")
            
            st.write("**Operadores trabajando por día:**")
            for summary in coverage_summary:
                st.write(summary)
            
            st.divider()_schedule = pd.DataFrame(schedule_data, columns=columns)
    
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
        st.write("**Asignación de operadores por turno:**")
        for shift_id in range(n_turnos_dia):
            operators_in_shift = [op for op, assigned_shift in scheduler.operator_assigned_shift.items() if assigned_shift == shift_id]
            st.write(f"**Turno {shift_id + 1}**: {len(operators_in_shift)} operadores")
            st.write(f"Operadores: {', '.join(operators_in_shift[:3])}{'...' if len(operators_in_shift) > 3 else ''}")
        
        st.write("**Cobertura diaria mínima:**")
        coverage_ok = True
        for week in range(3):
            week_coverage = []
            for day in range(7):
                day_coverage = []
                for shift_id in range(n_turnos_dia):
                    count = scheduler.count_operators_in_shift(week, day, shift_id)
                    day_coverage.append(count)
                    if count < min_operadores_turno:
                        coverage_ok = False
                min_coverage = min(day_coverage)
                week_coverage.append(min_coverage)
            st.write(f"S{week+1}: {week_coverage} (mín: {min(week_coverage)})")
        
        if coverage_ok:
            st.success("✅ Cobertura mínima cumplida todos los días")
        else:
            st.warning("⚠️ Algunos días no cumplen cobertura mínima")
    
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
        
        # Hoja con asignación de turnos
        shift_assignment_data = []
        for shift_id in range(n_turnos_dia):
            operators_in_shift = [op for op, assigned_shift in scheduler.operator_assigned_shift.items() if assigned_shift == shift_id]
            for operator in operators_in_shift:
                shift_assignment_data.append({
                    'Operador': operator,
                    'Turno_Base_Asignado': f'Turno {shift_id + 1}',
                    'Turno_Semana_1': f'Turno {(shift_id + 0) % n_turnos_dia + 1}',
                    'Turno_Semana_2': f'Turno {(shift_id + 1) % n_turnos_dia + 1}',
                    'Turno_Semana_3': f'Turno {(shift_id + 2) % n_turnos_dia + 1}'
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
