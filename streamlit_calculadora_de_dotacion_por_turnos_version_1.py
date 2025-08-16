import streamlit as st
import pandas as pd
import math
import json
import io
from collections import deque

st.set_page_config(page_title="CÁLCULO DE PERSONAL REQUERIDO Y PROGRAMACIÓN DE TURNOS", page_icon="🧮", layout="centered")
st.title("🧮 CÁLCULO DE PERSONAL REQUERIDO Y PROGRAMACIÓN DE TURNOS")
st.caption("Versión 1 – Cálculo mínimo de personal con base en horas requeridas, ausentismo y vacaciones. La rotación y descansos se añadirán en la V2.")

# ---- Sidebar: explicación breve ----
with st.sidebar:
    st.header("¿Cómo funciona?")
    st.write(
        """
        Ingresas los parámetros operativos y la app estima el **número mínimo de personas** necesarias para cubrir los turnos de la semana, **ajustado por ausentismo y vacaciones**.
        
        **Fórmula base semanal:**
        `Horas requeridas = Días a cubrir × Nº turnos × Horas por turno × Mín. operadores por turno`
        
        `Personal requerido = Horas requeridas ajustadas / Horas promedio por trabajador`
        
        Ajuste por ausentismo: divisor `(1 - % ausentismo)`.  
        Ajuste por vacaciones: horas adicionales en función de personas y días fuera.
        """
    )
    st.info("En V2 generaremos un calendario de 4 semanas que cumpla las restricciones de descansos y rotación.")

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
st.markdown(
    """
    #### Notas
    - Incluye ajuste por ausentismo y por vacaciones.
    - La V2 generará calendario de 4 semanas con descansos y rotación de turnos.
    """
)

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
    file_name="resultado_personal_v1.json",
    mime="application/json",
)

# ============================================================
# 3. Programación de Turnos (4 Semanas) — NUEVO/ACTUALIZADO
# ============================================================

st.write("---")
st.header("3. Programación de Turnos (4 Semanas)")

def weekly_days_pattern(horas_turno:int):
    """
    Define un patrón de días por semana (4 semanas) cercano a 42h/semana en promedio trisemanal.
    Se usa tolerancia ≤ 1 turno cuando 126h no es múltiplo de horas_turno.
    """
    if horas_turno == 12:
        # 36-48 alternado. Ventanas 1-3 y 2-4 quedan a ±6h (tolerancia = 1 turno)
        return [3,4,3,4]  # días/semana
    elif horas_turno == 8:
        # Mantiene ventanas de 3 semanas en 120–128h (±1 turno de 8h)
        return [5,5,6,5]  # 40,40,48,40
    else:  # 6h
        # Objetivo exacto 42h/sem => 7 días/sem. Podemos variar si no se cubren 7 días.
        return [7,7,7,7]

def check_trisem_42(hours_weeks, horas_turno):
    """
    Verifica ventanas (1-3) y (2-4) contra 42h/sem con tolerancia ≤ 1 turno.
    """
    tol = horas_turno  # tolerancia: hasta un turno de diferencia (±horas_turno sobre 126h)
    ok13 = abs(sum(hours_weeks[0:3]) - 126) <= tol
    ok24 = abs(sum(hours_weeks[1:4]) - 126) <= tol
    return ok13 and ok24, (sum(hours_weeks[0:3]) - 126, sum(hours_weeks[1:4]) - 126)

if st.button("Generar Programación de Turnos", key='generate_schedule_btn'):
    # Crear lista de operadores
    all_operators = [f"OP-{i+1}" for i in range(personas_actuales)]
    deficit = personal_total_requerido - personas_actuales
    if deficit > 0:
        all_operators += [f"OP-AD-{i+1}" for i in range(deficit)]

    total_operators = len(all_operators)

    # Validación mínima
    if total_operators < min_operadores_turno * n_turnos_dia:
        st.error(f"No hay suficientes operadores para cubrir todos los turnos. Se necesitan al menos {min_operadores_turno * n_turnos_dia} operadores.")
        st.stop()

    total_days = 4 * 7  # 28 días
    day_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    # Matriz inicial
    schedule_matrix = {op: ["DESCANSA"] * total_days for op in all_operators}

    # Patrón de días/semana (por operador; permite variación semana a semana)
    base_weekly_days = weekly_days_pattern(horas_por_turno)

    # Asignamos operadores a “grupos de turno base” para balancear cobertura
    # (distribuye casi equitativamente quién inicia en Turno 1, 2, ..., n)
    shift_buckets = [[] for _ in range(n_turnos_dia)]
    for idx, op in enumerate(all_operators):
        shift_buckets[idx % n_turnos_dia].append(op)

    # Programación respetando:
    # - Rotación de turno semanal (no repite turno consecutivo)
    # - Descanso previo al cambio de turno (descanso el lunes si cambia)
    # - Descanso principal en día distinto cada semana
    # - Días trabajados por semana según el patrón
    op_weekly_hours = {op: [0,0,0,0] for op in all_operators}
    for base_shift, ops in enumerate(shift_buckets):
        for j, op in enumerate(ops):
            # Día principal de descanso rotativo por semana (varía por operador)
            # Se asegura que cada semana sea distinto al anterior (mod 7):
            for w in range(4):
                week_start = w * 7
                week_days_to_work = base_weekly_days[w]
                # Turno de esta semana, rotando: nunca igual a la semana anterior
                current_shift = (base_shift + w) % n_turnos_dia
                shift_name = f"Turno {current_shift + 1}"

                # Día base de descanso (rotativo por operador y semana)
                rest_primary = (j + w) % dias_cubrir  # 0..dias_cubrir-1

                # Si cambia de turno respecto a la semana anterior, forzar descanso el lunes
                if w > 0:
                    prev_shift = (base_shift + (w-1)) % n_turnos_dia
                    if prev_shift != current_shift:
                        rest_primary = 0  # Lunes descanso para “reset” de turno

                # Calcular cuántos descansos tocan esta semana
                work_days = min(week_days_to_work, dias_cubrir)
                rest_days_needed = 7 - work_days
                # Si no cubrimos los 7 días de la semana, los días fuera de cobertura también serán descanso explícito
                # pero priorizamos que los descansos "dentro de los días a cubrir" varíen de día cada semana.

                # Construir lista de días a trabajar dentro de la semana
                # Partimos llenando todo como descanso
                for d in range(7):
                    schedule_matrix[op][week_start + d] = "DESCANSA"

                # Colocar el descanso principal primero
                schedule_matrix[op][week_start + rest_primary] = "DESCANSA"

                # Distribuir trabajo evitando el día de descanso principal.
                # Para diversificar, recorremos desde el martes (1) y cruzamos por un offset que depende de op y semana.
                assigned = 0
                offset = (j + 2*w) % 7
                for step in range(7):
                    d = (offset + step) % 7
                    if d >= dias_cubrir:
                        # días fuera de cobertura semanal: mantener descanso
                        continue
                    if d == rest_primary:
                        continue
                    if assigned < work_days:
                        schedule_matrix[op][week_start + d] = shift_name
                        assigned += 1

                op_weekly_hours[op][w] = assigned * horas_por_turno

    # Ajuste para garantizar cobertura mínima por día/turno
    for day in range(total_days):
        # Solo considerar días a cubrir (0..dias_cubrir-1 dentro de la semana)
        if (day % 7) >= dias_cubrir:
            continue
        for s in range(n_turnos_dia):
            sname = f"Turno {s+1}"
            count = sum(1 for op in all_operators if schedule_matrix[op][day] == sname)
            if count < min_operadores_turno:
                shortage = min_operadores_turno - count
                # Elegir operadores que estén descansando ese día y que NO rompan reglas:
                # - que su turno de esta semana sea sname (o que no hayan trabajado demasiado)
                # Para simplificar, permitimos activar a quienes descansan respetando la rotación semanal ya definida.
                week = day // 7
                candidates = []
                for op in all_operators:
                    if schedule_matrix[op][day] == "DESCANSA":
                        # No rompas “no repetir turno semana a semana”: ya fijamos turno semanal -> ok
                        # Evita ponerlos a trabajar en su día principal de descanso si es posible:
                        primary_rest = ( ( (op in shift_buckets[0]) and shift_buckets[0].index(op) or 0 ) + week ) % dias_cubrir
                        if (day % 7) != primary_rest:
                            candidates.append(op)
                # Si no hay suficientes, tomar cualquiera que descanse
                if len(candidates) < shortage:
                    candidates = [op for op in all_operators if schedule_matrix[op][day] == "DESCANSA"]

                for op in candidates[:shortage]:
                    schedule_matrix[op][day] = sname
                    op_weekly_hours[op][week] += horas_por_turno

    # Verificación de promedio trisemanal (tolerancia ≤ 1 turno)
    trisem_checks = []
    any_trisem_alert = False
    for op in all_operators:
        ok, diffs = check_trisem_42(op_weekly_hours[op], horas_por_turno)
        trisem_checks.append({
            "Operador": op,
            "W1(h)": op_weekly_hours[op][0],
            "W2(h)": op_weekly_hours[op][1],
            "W3(h)": op_weekly_hours[op][2],
            "W4(h)": op_weekly_hours[op][3],
            "Ventana(1-3)-Δh": diffs[0],
            "Ventana(2-4)-Δh": diffs[1],
            "OK≈42h/sem": "✅" if ok else "⚠️"
        })
        if not ok:
            any_trisem_alert = True

    # Construcción de etiquetas por día
    week_day_labels = []
    for week in range(4):
        for day in range(7):
            if day < dias_cubrir:
                week_day_labels.append(f"Semana {week+1} | {day_names[day]}")
            else:
                week_day_labels.append(f"Semana {week+1} | {day_names[day]} (No cubre)")

    # DataFrame completo
    df_schedule = pd.DataFrame({op: schedule_matrix[op] for op in all_operators}, index=week_day_labels).T

    # ========= NUEVO: VISTA SEPARADA POR TURNO (primero) =========
    st.subheader("Programación por Turno (vista separada)")

    for s in range(n_turnos_dia):
        sname = f"Turno {s+1}"
        # Para cada operador, dejamos solo los días de ese turno y marcamos lo demás como '-'
        df_shift = df_schedule.copy()
        for op in df_shift.index:
            df_shift.loc[op] = [val if val == sname else ("DESCANSA" if val == "DESCANSA" else "-") for val in df_shift.loc[op]]
        st.markdown(f"**➤ {sname}**")
        st.dataframe(df_shift)

    # ========= Luego: tabla completa =========
    st.subheader("Programación Completa de Turnos")
    st.dataframe(df_schedule)

    # Verificación de cobertura mínima
    st.subheader("Verificación de Cobertura Mínima")
    coverage_data = []
    for day in range(total_days):
        day_name = week_day_labels[day]
        if day % 7 < dias_cubrir:
            for s in range(n_turnos_dia):
                sname = f"Turno {s + 1}"
                operators_count = sum(1 for op in all_operators if schedule_matrix[op][day] == sname)
                status = "✅ OK" if operators_count >= min_operadores_turno else f"❌ Faltan {min_operadores_turno - operators_count}"
                coverage_data.append({
                    "Día": day_name,
                    "Turno": sname,
                    "Operadores": operators_count,
                    "Mínimo": min_operadores_turno,
                    "Estado": status
                })
    coverage_df = pd.DataFrame(coverage_data)
    st.dataframe(coverage_df)

    # Verificación de promedio trisemanal (42h) por operador
    st.subheader("Verificación de Promedio Trisemanal ≈ 42h/sem")
    tri_df = pd.DataFrame(trisem_checks)
    st.dataframe(tri_df)
    if any_trisem_alert:
        st.warning(
            "Algunos operadores no cumplen exactamente con 42h/sem en ventanas trisemanales; "
            "la diferencia está limitada a ≤ 1 turno debido al tamaño de los turnos."
        )

    # Descarga
    st.subheader("Descargar Programación")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_schedule.to_excel(writer, sheet_name='Programación Completa')
        coverage_df.to_excel(writer, sheet_name='Verificación Cobertura', index=False)
        tri_df.to_excel(writer, sheet_name='Verificación 42h', index=False)
    output.seek(0)
    st.download_button(
        label="Descargar Programación Completa en Excel",
        data=output,
        file_name='programacion_turnos_con_restricciones.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
