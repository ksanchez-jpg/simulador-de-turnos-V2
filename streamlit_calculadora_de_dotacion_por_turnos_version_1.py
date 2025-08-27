import pandas as pd
import itertools

# -------------------- CALENDARIO 2 SEMANAS --------------------
dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
dias_total = [f"{d} S1" for d in dias_semana] + [f"{d} S2" for d in dias_semana]

# -------------------- GENERAR PROGRAMACIÓN --------------------
def generar_programacion(operadores, config_turnos, min_operadores_turno):
    n_operadores = len(operadores)
    calendario = {op: ["Descanso"] * 14 for op in operadores}

    # Definir cuotas de trabajo por operador
    if "3 turnos" in config_turnos:  # 8h
        cuotas = ["8h"] * 9 + ["12h"]
    else:  # 12h
        cuotas = ["12h"] * 7

    # Repartir turnos de manera rotativa
    asignaciones = list(itertools.cycle(cuotas))
    idx = 0

    for dia in range(14):
        # asignar mínimo de operadores requeridos ese día
        for _ in range(min_operadores_turno):
            op = operadores[idx % n_operadores]
            # buscar la próxima cuota que tenga disponible
            while calendario[op][dia] != "Descanso":
                idx += 1
                op = operadores[idx % n_operadores]
            calendario[op][dia] = asignaciones[idx % len(asignaciones)]
            idx += 1

    # Convertir a DataFrame
    df = pd.DataFrame.from_dict(calendario, orient="index", columns=dias_total)
    df.index.name = "Operador"
    df.reset_index(inplace=True)

    return df

# -------------------- USO --------------------
operadores = [f"Op{i+1}" for i in range(personal_total_requerido)]
df_programacion = generar_programacion(operadores, config_turnos, min_operadores_turno)

st.subheader("📅 Calendario de 2 semanas")
st.dataframe(df_programacion, use_container_width=True)
