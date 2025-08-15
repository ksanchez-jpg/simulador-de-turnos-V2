import pandas as pd
from io import BytesIO

# === CONFIGURACIÓN DESDE TU SELECTBOX EXISTENTE ===
turno_opcion = st.selectbox(
    "Configuración de turnos",
    ["3 turnos de 8 horas", "2 turnos de 12 horas", "4 turnos de 6 horas"]
)

if turno_opcion == "3 turnos de 8 horas":
    num_turnos = 3
    horas_turno = 8
elif turno_opcion == "2 turnos de 12 horas":
    num_turnos = 2
    horas_turno = 12
else:
    num_turnos = 4
    horas_turno = 6

# === FUNCIÓN PARA GENERAR PROGRAMACIÓN ===
def generar_programacion(num_turnos, horas_turno, operadores_totales):
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    semanas = 4
    horas_semanales = 42
    horas_totales_4s = horas_semanales * semanas
    horas_diarias = horas_turno

    tablas = {}
    operadores = [f"OP{i+1}" for i in range(operadores_totales)]
    adicionales_count = 0

    for turno in range(1, num_turnos + 1):
        data = []
        for op in operadores:
            fila = {"Operador": op}
            turno_actual = (turno + operadores.index(op)) % num_turnos + 1
            dias_descanso = set()
            horas_acumuladas = 0

            for semana in range(semanas):
                # Rotación semanal
                turno_semana = ((turno_actual - 1 + semana) % num_turnos) + 1
                for dia in dias_semana:
                    if semana > 0 and dia == "Lunes" and not descanso_previo:
                        fila[f"Semana {semana+1} - {dia}"] = f"Turno{turno_semana}"
                        horas_acumuladas += horas_diarias
                    else:
                        if len(dias_descanso) < semanas:
                            dias_descanso.add(dia)
                            adicionales_count += 1
                            fila[f"Semana {semana+1} - {dia}"] = f"Descansa (OP-AD{adicionales_count})"
                        else:
                            fila[f"Semana {semana+1} - {dia}"] = f"Turno{turno_semana}"
                            horas_acumuladas += horas_diarias
                descanso_previo = dia in dias_descanso
            data.append(fila)
        tablas[f"Turno {turno}"] = pd.DataFrame(data)
    return tablas

# === LLAMADA A LA FUNCIÓN USANDO TU CÁLCULO EXISTENTE ===
# Aquí 'operadores_totales' DEBE venir de tu cálculo previo
tablas = generar_programacion(num_turnos, horas_turno, operadores_totales)

# === MOSTRAR Y DESCARGAR TABLAS ===
for nombre_turno, df in tablas.items():
    st.subheader(nombre_turno)
    st.dataframe(df)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    excel_data = output.getvalue()

    st.download_button(
        label=f"📥 Descargar {nombre_turno}",
        data=excel_data,
        file_name=f"{nombre_turno}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
