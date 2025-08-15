import pandas as pd
import streamlit as st
from io import BytesIO

# --- CONFIGURACIÓN DE TURNOS ---
opcion_turnos = st.selectbox(
    "Configuración de turnos",
    ["3 turnos de 8 horas", "2 turnos de 12 horas", "4 turnos de 6 horas"]
)

if opcion_turnos == "3 turnos de 8 horas":
    n_turnos_dia = 3
    horas_por_turno = 8
elif opcion_turnos == "2 turnos de 12 horas":
    n_turnos_dia = 2
    horas_por_turno = 12
elif opcion_turnos == "4 turnos de 6 horas":
    n_turnos_dia = 4
    horas_por_turno = 6

# --- ENTRADA DE PERSONAL ---
personal_total = st.number_input(
    "Cantidad total de personal",
    min_value=1,
    step=1
)

# --- FUNCIÓN PARA GENERAR PROGRAMACIÓN ---
def generar_programacion(n_turnos, horas_turno, personal):
    tablas = []
    for turno in range(1, n_turnos + 1):
        data = {"Semana": [1, 2, 3, 4],
                "Turno": [turno] * 4,
                "Horas por turno": [horas_turno] * 4,
                "Personal asignado": [personal // n_turnos] * 4}
        df = pd.DataFrame(data)
        tablas.append(df)
    return tablas

# --- BOTÓN PARA GENERAR Y DESCARGAR ---
if st.button("Generar programación"):
    try:
        tablas = generar_programacion(n_turnos_dia, horas_por_turno, personal_total)
        
        # Mostrar tablas en pantalla
        for idx, tabla in enumerate(tablas, 1):
            st.subheader(f"Turno {idx}")
            st.dataframe(tabla)

        # Guardar en Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            for idx, tabla in enumerate(tablas, 1):
                tabla.to_excel(writer, sheet_name=f"Turno_{idx}", index=False)
        output.seek(0)

        st.download_button(
            label="📥 Descargar programación en Excel",
            data=output,
            file_name="programacion_4semanas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except NameError as e:
        st.error(f"Error al generar la programación: {e}")
