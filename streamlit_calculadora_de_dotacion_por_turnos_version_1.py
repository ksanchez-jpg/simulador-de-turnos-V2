# --- PROGRAMACIÓN DE TURNOS (V2) ---
import pandas as pd
from io import BytesIO

def generar_programacion(num_turnos, horas_turno, operadores_totales):
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    semanas = 4
    horas_max_trisemanal = 42
    horas_diarias = horas_turno

    tablas = {}
    operadores = [f"OP{i+1}" for i in range(operadores_totales)]
    adicionales_count = 0

    for turno in range(1, num_turnos + 1):
        data = []
        for idx, op in enumerate(operadores):
            fila = {"Operador": op}
            dias_descanso = set()
            horas_acumuladas = 0

            for semana in range(semanas):
                turno_semana = ((turno - 1 + idx + semana) % num_turnos) + 1
                for dia in dias_semana:
                    # Regla de descanso: al menos 1 día libre en 7
                    if len(dias_descanso) < semana + 1 and (dia == "Domingo" or horas_acumuladas >= horas_max_trisemanal):
                        adicionales_count += 1
                        fila[f"Semana {semana+1} - {dia}"] = f"Descansa (OP-AD{adicionales_count})"
                        dias_descanso.add(dia)
                    else:
                        fila[f"Semana {semana+1} - {dia}"] = f"Turno{turno_semana}"
                        horas_acumuladas += horas_diarias

            data.append(fila)
        tablas[f"Turno {turno}"] = pd.DataFrame(data)
    return tablas

# Usamos los valores que ya calculaste arriba
tablas = generar_programacion(n_turnos_dia, horas_por_turno, personal_total_requerido)

st.subheader("📅 Programación de turnos (4 semanas)")
for nombre_turno, df in tablas.items():
    st.markdown(f"**{nombre_turno}**")
    st.dataframe(df)

    # Botón descarga Excel por turno
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
