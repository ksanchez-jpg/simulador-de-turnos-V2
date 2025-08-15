# ----------------- INICIO: BLOQUE DE PROGRAMACIÓN (pegar AL FINAL del archivo) -----------------
import pandas as pd
from io import BytesIO
from itertools import cycle
import math

def generar_programacion(n_turnos, horas_por_turno, personal_total_requerido,
                         min_operadores_turno, personas_actuales):
    """
    Genera tablas por turno con 4 semanas seguidas.
    Usa:
      - n_turnos: número de turnos (2,3 o 4)
      - horas_por_turno: 8,12 o 6
      - personal_total_requerido: total sobre el que programar (ceil que ya calculaste)
      - min_operadores_turno: mínimo requerido por turno (para cubrir con AD si hace falta)
      - personas_actuales: número de operadores reales (los adicionales serán OP-AD1..)
    Retorna dict: {turno_num: DataFrame}, y DataFrame resumen.
    """
    # Config
    semanas = 4
    dias = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]

    # Construir lista de operadores: primarios (OP1..OPn_actuales) + adicionales (OP-AD1..)
    primarios = [f"OP{idx+1}" for idx in range(personas_actuales)]
    ad_count = max(0, personal_total_requerido - personas_actuales)
    ads = [f"OP-AD{idx+1}" for idx in range(ad_count)]
    pool_ids = primarios + ads  # lista completa sobre la cual se programa

    # Turno de inicio por operador (distribución equitativa)
    start_shift = {w: (i % n_turnos) + 1 for i, w in enumerate(pool_ids)}

    # Calcular patrón de turnos deseado por semana (número de días trabajados)
    # Queremos aproximar el promedio trisemanal de 42h:
    avg_shifts_per_week = 42.0 / horas_por_turno
    desired_total_shifts_4w = int(round(avg_shifts_per_week * 4))
    base = desired_total_shifts_4w // 4
    rem = desired_total_shifts_4w % 4
    week_shifts = [base + (1 if i < rem else 0) for i in range(4)]
    # Ejemplo: para 8h -> avg_shifts_per_week=5.25 -> desired_total_4w=21 -> [6,5,5,5] (suma 21)

    # Estructuras
    schedule = {w: {wk+1: {d: False for d in dias} for wk in range(semanas)} for w in pool_ids}
    shift_by_week = {w: {wk+1: None for wk in range(semanas)} for w in pool_ids}

    # Construir schedule por trabajador
    for idx, w in enumerate(pool_ids):
        s = start_shift[w]
        # shift por semana (rotación cíclica, solo cambian entre semanas)
        for wk in range(1, semanas+1):
            shift_by_week[w][wk] = ((s - 1 + (wk-1)) % n_turnos) + 1

        # asignar qué días trabaja cada semana según week_shifts, cuidando reglas:
        for wk in range(1, semanas+1):
            workdays = week_shifts[wk-1]
            free_needed = 7 - workdays
            # rotar la posición de los días libres para variar entre operadores
            start_rot = (idx + wk - 1) % 7
            cand_free = []
            i = 0
            while len(cand_free) < free_needed:
                day = dias[(start_rot + i) % 7]
                if day not in cand_free:
                    cand_free.append(day)
                i += 1
            # Si hay cambio de turno la siguiente semana, forzar domingo libre en la semana actual
            if wk < semanas and shift_by_week[w][wk] != shift_by_week[w][wk+1]:
                if "Domingo" not in cand_free:
                    # mantener cantidad de libres: reemplazamos el último candidato por Domingo
                    cand_free[-1] = "Domingo"
            # marcar
            for d in dias:
                schedule[w][wk][d] = False if d in cand_free else True

    # Asegurar al menos 1 domingo libre en las 4 semanas por trabajador
    for w in pool_ids:
        sundays_off = sum(1 for wk in range(1, semanas+1) if not schedule[w][wk]["Domingo"])
        if sundays_off == 0:
            # forzar domingo libre en la primera semana posible, respetando el patrón lo más posible
            for wk in range(1, semanas+1):
                # si actualmente trabaja domingo, convierte en libre y convierte un día libre en trabajo para mantener conteo
                if schedule[w][wk]["Domingo"]:
                    off_days = [d for d in dias if not schedule[w][wk][d]]
                    if off_days:
                        swap = off_days[0]
                        schedule[w][wk][swap] = True
                        schedule[w][wk]["Domingo"] = False
                    else:
                        # si no hay off (caso raro), simplemente marcar domingo off
                        schedule[w][wk]["Domingo"] = False
                    break

    # Construir asignación por (semana,dia,turno)
    assignment = {wk: {d: {t: [] for t in range(1, n_turnos+1)} for d in dias} for wk in range(1, semanas+1)}
    for wk in range(1, semanas+1):
        for d in dias:
            for w in pool_ids:
                if schedule[w][wk][d]:
                    t = shift_by_week[w][wk]
                    assignment[wk][d][t].append(w)

    # Cubrir huecos con ADs preferentemente en su día de descanso
    ad_list = [p for p in pool_ids if p.startswith("OP-AD")]
    ad_cycle = cycle(ad_list) if ad_list else None
    covers = {}  # covers[(wk,d,t)] = [ADs]
    for wk in range(1, semanas+1):
        for d in dias:
            for t in range(1, n_turnos+1):
                covers[(wk,d,t)] = []
                cur = assignment[wk][d][t]
                if len(cur) < min_operadores_turno:
                    need = min_operadores_turno - len(cur)
                    assigned = 0
                    if ad_cycle is not None:
                        # preferir ADs que estén en descanso ese día (son reemplazos reales)
                        for _ in range(len(ad_list)):
                            c = next(ad_cycle)
                            if not schedule[c][wk][d] and c not in covers[(wk,d,t)]:
                                covers[(wk,d,t)].append(c)
                                assigned += 1
                                if assigned >= need:
                                    break
                        # si aún faltan, asignar ADs disponibles aunque estén trabajando (overflow)
                        while assigned < need and ad_list:
                            c = next(ad_cycle)
                            if c not in covers[(wk,d,t)]:
                                covers[(wk,d,t)].append(c)
                                assigned += 1
                    assignment[wk][d][t].extend(covers[(wk,d,t)])

    # Construir tablas por turno (cada tabla contiene los operadores cuyo turno inicial == t)
    tables_by_turn = {}
    for t in range(1, n_turnos+1):
        owned = [w for w in pool_ids if start_shift[w] == t]
        # ordenar primarios antes que ADs
        owned_sorted = sorted(owned, key=lambda x: (x.startswith("OP-AD"), x))
        rows = []
        for w in owned_sorted:
            row = {"Operador": w}
            for wk in range(1, semanas+1):
                for d in dias:
                    col = f"S{wk}-{d}"
                    # Si el trabajador trabaja ese día y ese día su turno coincide con esta tabla -> Turno t
                    if schedule[w][wk][d] and shift_by_week[w][wk] == t:
                        row[col] = f"Turno {t}"
                    else:
                        # si descansa y existe AD que cubre ese turno/dia -> indicar primer AD
                        cover_list = covers.get((wk, d, t), [])
                        if (not schedule[w][wk][d]) and cover_list:
                            row[col] = f"Descansa ({cover_list[0]})"
                        else:
                            row[col] = "Descansa"
            rows.append(row)
        cols = ["Operador"] + [f"S{wk}-{d}" for wk in range(1, semanas+1) for d in dias]
        df = pd.DataFrame(rows, columns=cols)
        tables_by_turn[t] = df

    # resumen por operador (horas semanales y dominos libres)
    summary_rows = []
    for w in pool_ids:
        weekly_hours = []
        for wk in range(1, semanas+1):
            workdays = sum(1 for d in dias if schedule[w][wk][d])
            weekly_hours.append(workdays * horas_por_turno)
        summary_rows.append({
            "Operador": w,
            "ShiftStart": start_shift[w],
            "Horas_Sem1": weekly_hours[0],
            "Horas_Sem2": weekly_hours[1],
            "Horas_Sem3": weekly_hours[2],
            "Horas_Sem4": weekly_hours[3],
            "Sum_3w_1_3": sum(weekly_hours[0:3]),
            "Sum_3w_2_4": sum(weekly_hours[1:4]),
            "Domingos_libres": sum(1 for wk in range(1, semanas+1) if not schedule[w][wk]["Domingo"])
        })
    df_summary = pd.DataFrame(summary_rows)

    return tables_by_turn, df_summary

# ----------------- EJECUCIÓN: usar variables calculadas en tu script -----------------
try:
    tablas, resumen = generar_programacion(
        n_turnos=n_turnos_dia,
        horas_por_turno=horas_por_turno,
        personal_total_requerido=personal_total_requerido,
        min_operadores_turno=min_operadores_turno,
        personas_actuales=personas_actuales
    )
except NameError as e:
    # Si alguna variable no existe, muestra un mensaje claro
    st.error("Error al generar la programación: una variable necesaria no está definida. "
             "Asegúrate de que estás pegando este bloque al final del archivo, "
             "después de que se calculen `n_turnos_dia`, `horas_por_turno`, "
             "`personal_total_requerido`, `min_operadores_turno` y `personas_actuales`.")
    st.exception(e)
else:
    st.subheader("📅 Programación de turnos (4 semanas)")
    # Mostrar cada tabla y permitir descarga individual
    for t, df in tablas.items():
        st.markdown(f"**Turno {t}**")
        st.dataframe(df)
        # descarga individual
        out = BytesIO()
        with pd.ExcelWriter(out, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=f"Turno_{t}")
        st.download_button(
            label=f"📥 Descargar Turno {t} (Excel)",
            data=out.getvalue(),
            file_name=f"turno_{t}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # además, crear un solo archivo Excel con todas las hojas (más cómodo)
    out_all = BytesIO()
    with pd.ExcelWriter(out_all, engine="openpyxl") as writer:
        for t, df in tablas.items():
            sheet_name = f"Turno_{t}"
            # Excel no permite nombres demasiado largos: acortar si hace falta
            df.to_excel(writer, index=False, sheet_name=sheet_name[:31])
        resumen.to_excel(writer, index=False, sheet_name="Resumen")
    st.download_button(
        label="📥 Descargar TODO (todas las tablas en un solo Excel)",
        data=out_all.getvalue(),
        file_name="programacion_4semanas_turnos.xlsx"

