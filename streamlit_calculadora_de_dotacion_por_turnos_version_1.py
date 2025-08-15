import streamlit as st
import pandas as pd
import math

# -----------------------------
# Función para generar la programación
# -----------------------------
def generar_programacion(num_turnos, horas_turno, operadores_totales):
    semanas = 4
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    
    # Nombres de operadores
    operadores = [f"OP{i+1}" for i in range(operadores_totales)]
    
    # Distribución inicial de operadores entre turnos
    base_por_turno = operadores_totales // num_turnos
    extras = operadores_totales % num_turnos
    operadores_por_turno = []
    start = 0
    for t in range(num_turnos):
        end = start + base_por_turno + (1 if t < extras else 0)
        operadores_por_turno.append(operadores[start:end])
        start = end

    # Programación por turno
    tablas_turnos = {}
    op_ad_count = 1

    for turno_inicial in range(1, num_turnos+1):
        filas = []
        for op in operadores_por_turno[turno_inicial-1]:
            fila = {"Operador": op}
            turno_actual = turno_inicial
            dias_descanso_usados = []
            for semana in range(1, semanas+1):
                # Seleccionar día de descanso (distinto cada semana)
                dia_descanso = dias_semana[(semana - 1) % len(dias_semana)]
                while dia_descanso in dias_descanso_usados:
                    dia_descanso = dias_semana[(dias_semana.index(dia_descanso) + 1) % len(dias_semana)]
                dias_descanso_usados.append(dia_descanso)

                for dia in dias_semana:
                    col = f"S{semana}-{dia}"
                    if dia == dia_descanso:
                        fila[col] = f"Descansa (OP-AD{op_ad_count})"
                        op_ad_count += 1
                    else:
                        if semana == 1:
                            fila[col] = f"Turno {turno_actual}"
                        else:
                            # Cambio de turno solo después de descanso
                            if dia == "Lunes" and dias_semana[dias_semana.index(dia) - 1] == dia_descanso:
                                turno_actual = (turno_actual % num_turnos) + 1
                            fila[col] = f"Turno {turno_actual}"
            filas.append(fila)
        
        df_turno = pd.DataFrame(filas)
        tablas_turnos[turno_inicial] = df_turno
    
    return tablas_turnos


# -----------------------------
# Configuración desde selector
# -----------------------------
config = st.selectbox("Configuración de turnos", ["3 turnos de 8 horas", "2 turnos de 12 horas", "4 turnos de 6 horas"])

if config.startswith("3"):
    num_turnos, horas_turno = 3, 8
elif config.startswith("2"):
    num_turnos, horas_turno = 2, 12
else:
    num_turnos, horas_turno = 4, 6

# Ejemplo: aquí deberías poner tu cálculo real de operadores necesarios
operadores_totales = st.number_input("Operadores totales requeridos", min_value=1, value=18)

if st.button("Generar programación"):
    tablas = generar_programacion(num_turnos, horas_turno, operadores_totales)
    for turno, df in tablas.items():
        st.subheader(f"Turno {turno}")
        st.dataframe(df)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(f"Descargar Turno {turno}", data=csv, file_name=f"turno_{turno}.csv", mime="text/csv")
