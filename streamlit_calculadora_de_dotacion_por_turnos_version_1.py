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
horas_promedio_semanal = st.number_input("Horas promedio semanales por operador (últimas 2 semanas)", min_value=1, value=48)
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
                personal_final_necesario = math.ceil(personal_ajustado_ausentismo + personal_vacaciones)
                
                # 5. Calcular la brecha de personal (si la hay)
                diferencia_personal = personal_final_necesario - personal_actual

                # --- Sección de Resultados ---
                st.header("Resultados del Cálculo")
                st.metric(label="Personal Requerido para no generar horas extras", value=f"{personal_final_necesario} persona(s)")
                st.metric(label=f"Horas de trabajo totales requeridas a la semana para {cargo}", value=f"{horas_trabajo_totales_semanales} horas")
                
                # Mostrar la brecha de personal
                if diferencia_personal > 0:
                    st.warning(f"Se necesitan **{diferencia_personal}** personas adicionales para cubrir la operación.")
                elif diferencia_personal < 0:
                    st.info(f"Tienes **{abs(diferencia_personal)}** personas de más, lo que podría reducir costos o permitir más personal de reserva.")
                else:
                    st.success("¡El personal actual es el ideal para esta operación!")
                
                # --- Programación de Turnos Sugerida ---
                st.header("Programación de Turnos Sugerida (basada en el personal requerido)")
                if personal_final_necesario > 0:
                    turnos_por_dia = []
                    # Generar los turnos de inicio y fin
                    for i in range(cantidad_turnos):
                        hora_inicio = i * horas_por_turno
                        hora_fin = (hora_inicio + horas_por_turno) % 24
                        turnos_por_dia.append(f"{hora_inicio:02d}:00 - {hora_fin:02d}:00")

                    # Distribuir el personal en las 3 tablas de forma secuencial
                    empleados_por_turno_base = personal_final_necesario // cantidad_turnos
                    resto_empleados = personal_final_necesario % cantidad_turnos

                    start_idx = 0
                    for i in range(cantidad_turnos):
                        st.subheader(f"Tabla Turno {i + 1}: {turnos_por_dia[i]}")
                        
                        # Calcular el número de empleados para este turno
                        num_empleados_este_turno = empleados_por_turno_base
                        if i < resto_empleados:
                            num_empleados_este_turno += 1

                        if num_empleados_este_turno > 0:
                            # Crear un DataFrame para la tabla
                            data = {
                                'Operador': [f"{cargo} {j + 1}" for j in range(start_idx, start_idx + num_empleados_este_turno)],
                            }
                            # Agregar los días de la semana como columnas
                            for dia in range(dias_a_cubrir):
                                data[f'Día {dia + 1}'] = ['Turno {}'.format(i + 1)] * num_empleados_este_turno
                            
                            df = pd.DataFrame(data)
                            st.dataframe(df, hide_index=True, use_container_width=True)
                            
                            start_idx += num_empleados_este_turno
                        else:
                            st.info(f"No hay personal asignado para el Turno {i + 1}.")

                else:
                    st.info("No se necesita personal para la operación, por lo que no se genera una programación de turnos.")
    
    except Exception as e:
        st.error(f"Ha ocurrido un error en el cálculo. Por favor, revise los valores ingresados. Error: {e}")
