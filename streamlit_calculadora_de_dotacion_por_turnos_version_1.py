import pandas as pd
from io import BytesIO

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
                        # Cambio de turno después de descanso
                        if dia == "Lunes" and dias_semana[dias_semana.index(dia) - 1] == dia_descanso:
                            turno_actual = (turno_actual % num_turnos) + 1
                        fila[col] = f"Turno {turno_actual}"
            filas.append(fila)
        
        df_turno = pd.DataFrame(filas)
        tablas_turnos[turno_inicial] = df_turno
    
    return tablas_turnos

# -----------------------------
# Generar programación y mostrar/descargar
# -----------------------------
tablas = generar_programacion(num_turnos, horas_turno, operadores_totales)

for turno, df in tablas.items():
    st.subheader(f"Programación Turno {turno}")
    st.dataframe(df)

    # Convertir a Excel en memoria
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=f"Turno {turno}")
    excel_data = output.getvalue()

    st.download_button(
        label=f"📥 Descargar Turno {turno} en Excel",
        data=excel_data,
        file_name=f"turno_{turno}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

