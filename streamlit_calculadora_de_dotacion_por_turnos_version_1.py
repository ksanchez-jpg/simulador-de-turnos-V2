import streamlit as st
import math
import pandas as pd

# Título de la aplicación
st.title("Calculadora de Personal y Programación de Turnos")
st.write("Ingrese los parámetros a continuación para calcular el personal necesario y generar la programación de turnos.")

# --- Sección de Parámetros de Entrada ---
st.header("Parámetros de la Programación")

# Campos de entrada de texto para el cargo
cargo = st.text_input("Cargo del personal (ej: Operador de Máquina)", "Operador")

# Campos de entrada numéricos con valores mínimos y máximos
personal_actual = st.number_input("Cantidad de personal actual en el cargo", min_value=0, value=1)
ausentismo_porcentaje = st.number_input("Porcentaje de ausentismo (%)", min_value=0.0, max_value=100.0, value=5.0)
dias_a_cubrir = st.number_input("Días a cubrir por semana", min_value=1, max_value=7, value=7)
horas_promedio_semanal = st.number_input("Horas promedio semanales por operador (últimas 3 semanas)", min_value=1, value=42)
personal_vacaciones = st.number_input("Personal de vacaciones en el período de programación", min_value=0, value=0)
operadores_por_turno = st.number_input("Cantidad de operadores requeridos por turno", min_value=1, value=1)

# Selección de turnos y validación de horas por turno
st.subheader("Configuración de Turnos")
cantidad_turnos = st.selectbox("Cantidad de turnos", [2, 3], index=1)
if cantidad_turnos == 3:
    horas_por_turno = 8
    st.write("Horas por turno (automático): 8 horas (para 3 turnos)")
else:
    horas_por_turno = 12
    st.write("Horas por turno (automático): 12 horas (para 2 turnos)")

# --- Botón para Iniciar el Cálculo ---
if st.button("Calcular Personal Necesario y Turnos"):
    try:
        # Validación de valores para evitar errores de cálculo
        if personal_actual <= 0 or dias_a_cubrir <= 0 or horas_promedio_semanal <= 0 or operadores_por_turno <= 0:
            st.error("Por favor, ingrese valores válidos mayores a cero.")
        else:
            # --- Lógica de Cálculo ---
            
            # 1. Calcular las horas de trabajo totales requeridas por semana
            horas_operacion_diarias = cantidad_turnos * horas_por_turno
            horas_trabajo_totales_semanales = dias_a_cubrir * horas_operacion_diarias * operadores_por_turno
            
            # 2. Calcular el personal teórico necesario (sin ausentismo/vacaciones)
            personal_teorico = horas_trabajo_totales_semanales / horas_promedio_semanal
            
            # 3. Ajustar el personal por ausentismo
            factor_ausentismo = 1 - (ausentismo_porcentaje / 100)
            if factor_ausentismo <= 0:
                 st.error("El porcentaje de ausentismo no puede ser 100% o más. Por favor, ajuste el valor.")
            else:
                personal_ajustado_ausentismo = personal_teorico / factor_ausentismo
                
                # 4. Sumar el personal de vacaciones
                personal_final_necesario = round(personal_ajustado_ausentismo + personal_vacaciones)
                
                # 5. Calcular la brecha de personal (si la hay)
                diferencia_personal = personal_final_necesario - personal_actual
                
                # Validar que el personal necesario sea suficiente para cubrir los turnos
                if personal_final_necesario < operadores_por_turno * cantidad_turnos:
                    st.error(f"Error: El personal requerido ({personal_final_necesario}) no es suficiente para cubrir los {operadores_por_turno} operadores por turno en {cantidad_turnos} turnos.")
                else:
                    # --- Sección de Resultados ---
                    st.header("Resultados del Cálculo")
                    
                    # Usamos una columna para los resultados y otra para la explicación
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(label="Personal Requerido para no generar horas extras", value=f"{personal_final_necesario} persona(s)")
                        st.metric(label=f"Horas de trabajo totales requeridas a la semana para {cargo}", value=f"{horas_trabajo_totales_semanales} horas")
                    with col2:
                        st.markdown("---")
                        st.markdown("**Cómo se calcula el personal requerido:**")
                        st.markdown(f"1. **Horas totales:** `{dias_a_cubrir} (días) * {horas_operacion_diarias} (horas/día) * {operadores_por_turno} (op/turno) = {horas_trabajo_totales_semanales} (horas totales)`")
                        st.markdown(f"2. **Personal teórico:** `{horas_trabajo_totales_semanales} (horas totales) / {horas_promedio_semanal} (horas/op) = {personal_teorico:.2f} (personal teórico)`")
                        st.markdown(f"3. **Ajuste:** `({personal_teorico:.2f} / (1 - {ausentismo_porcentaje}/100)) + {personal_vacaciones} (vacaciones)`")
                        st.markdown(f"4. **Resultado final:** `{round(personal_ajustado_ausentismo + personal_vacaciones)} (personal redondeado)`")
                        st.markdown("---")
                    
                    # Mostrar la brecha de personal
                    if diferencia_personal > 0:
                        st.warning(f"Se necesitan **{diferencia_personal}** personas adicionales para cubrir la operación.")
                    elif diferencia_personal < 0:
                        st.info(f"Tienes **{abs(diferencia_personal)}** personas de más, lo que podría reducir costos o permitir más personal de reserva.")
                    else:
                        st.success("¡El personal actual es el ideal para esta operación!")
                    
                    # --- Programación de Turnos Sugerida con Descanso Rotativo y Balance de Horas ---

                import streamlit as st
import pandas as pd
import random

# Definición de la programación semanal
programacion = {
    "Semana A": [12, 12, 12, 12, 12, 0, 0],  # 4 turnos de 12h
    "Semana B": [8, 8, 8, 8, 8, 8, 0],      # 6 turnos de 8h
    "Semana C": [12, 12, 8, 8, 0, 0, 0]     # 2 turnos de 12h + 2 turnos de 8h
}

# Función para generar la programación
def generar_programacion(operadores):
    semanas = ["Semana A", "Semana B", "Semana C"]
    data = []

    for i, op in enumerate(operadores):
        semana = semanas[i % len(semanas)]  # Rota entre A, B, C
        horas = programacion[semana]
        total_horas = sum(horas)
        data.append({
            "Operador": op,
            "Semana": semana,
            "Turnos": horas,
            "Total Horas": total_horas
        })

    return pd.DataFrame(data)

# Interfaz en Streamlit
st.title("📅 Generador de Programación de Turnos")
st.write("Modelo de turnos con promedio de **41.33 horas semanales** en 3 semanas.")

# Input: número de operadores
num_operadores = st.number_input("Número de operadores", min_value=1, value=6)

# Crear lista de operadores
operadores = [f"Operador {i+1}" for i in range(num_operadores)]

# Generar programación
df = generar_programacion(operadores)

# Mostrar tabla
st.dataframe(df)

# Exportar a Excel
if st.button("Exportar a Excel"):
    df.to_excel("programacion_turnos.xlsx", index=False)
    st.success("Archivo 'programacion_turnos.xlsx' generado con éxito 🎉")
