import streamlit as st
import pandas as pd
import math
import io
from collections import defaultdict, deque

# -------------------- CONFIGURACIÓN --------------------
st.set_page_config(page_title="Cálculo y Programación de Turnos", page_icon="🧮", layout="wide")
st.title("🧮 CÁLCULO DE PERSONAL REQUERIDO Y PROGRAMACIÓN BI-SEMANAL")
st.caption("Introduce parámetros, calcula dotación y genera la programación (matriz operadores x días S1/S2).")

# -------------------- INPUTS --------------------
with st.sidebar:
    st.header("Parámetros")
    cargo = st.text_input("Nombre del cargo", value="Operador")
    personas_actuales = st.number_input("Total de personas actuales en el cargo (0 = usar requerido)", min_value=0, value=0, step=1)
    min_operadores_turno = st.number_input("Cantidad mínima de operadores por turno", min_value=1, value=3, step=1)
    dias_cubrir = st.number_input("Días a cubrir en la semana (1-7)", min_value=1, max_value=7, value=7, step=1)
    config_turnos = st.selectbox("Configuración de turnos", ("3 turnos de 8 horas", "2 turnos de 12 horas"))
    ausentismo_pct = st.number_input("% de ausentismo", min_value=0.0, max_value=99.0, value=8.0, step=0.5)
    horas_prom_bisem = st.number_input("Horas por semana (promedio bisemanal)", min_value=1.0, max_value=120.0, value=42.0, step=0.5)
    personal_vacaciones = st.number_input("Personal de vacaciones (esta quincena)", min_value=0, value=0, step=1)
    dias_vacaciones = st.number_input("Días de vacaciones por persona (esta quincena)", min_value=0, value=0, step=1)
    # Día 12h seleccionable para 3x8 (si se cubren menos de 3 días, el control adapta)
    dias_nombre = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
    dias_disponibles = dias_nombre[:dias_cubrir]
    dia_12h_choice = st.selectbox("Día 12H (solo 3x8, semana 2)", options=dias_disponibles, index=min(2, len(dias_disponibles)-1))
    ejecutar = st.button("Generar cálculo y programación")

# -------------------- PREPARAR PARÁMETROS --------------------
if "3 turnos" in config_turnos:
    esquema = "3x8"
    n_turnos_dia_base = 3
    horas_por_turno_base = 8
else:
    esquema = "2x12"
    n_turnos_dia_base = 2
    horas_por_turno_base = 12

# -------------------- CÁLCULOS DE DOTACIÓN --------------------
# Horas requeridas por semana (demanda total mínima para cubrir la operación)
# Se asume: demanda diaria = n_turnos_dia_base * horas_por_turno_base * min_operadores_turno
horas_semana_requeridas = dias_cubrir * n_turnos_dia_base * horas_por_turno_base * min_operadores_turno

factor_disponibilidad = 1.0 - (ausentismo_pct / 100.0)
if factor_disponibilidad <= 0:
    st.error("El % de ausentismo no puede ser 100% o más.")
    st.stop()

horas_semana_ajustadas = horas_semana_requeridas / factor_disponibilidad
personal_requerido_base = horas_semana_ajustadas / horas_prom_bisem

# Vacaciones: computar pérdida de horas en la quincena (promedio por día de cobertura)
horas_dia_promedio = horas_prom_bisem / max(1, dias_cubrir)
horas_vacaciones = personal_vacaciones * dias_vacaciones * horas_dia_promedio
personal_requerido_vacaciones = horas_vacaciones / horas_prom_bisem

personal_total_requerido = math.ceil(personal_requerido_base + personal_requerido_vacaciones)
brecha = personal_total_requerido - personas_actuales

# Mostrar métricas arriba
st.subheader("📊 Resultados del cálculo")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Personal requerido (sin vacaciones)", f"{math.ceil(personal_requerido_base)}")
c2.metric("Adicional por vacaciones (eq.)", f"{math.ceil(personal_requerido_vacaciones)}")
c3.metric("Total personal necesario", f"{personal_total_requerido}")
c4.metric("Brecha", f"{brecha:+}")

st.markdown(f"**Esquema seleccionado:** {esquema}  •  **Días a cubrir:** {dias_cubrir}")

# -------------------- GENERAR PROGRAMACIÓN (al pulsar botón) --------------------
if ejecutar:
    # Número de operadores a programar: si el usuario indica >0 usamos ese personal, else usamos el requerido
    num_personas = personas_actuales if personas_actuales > 0 else personal_total_requerido
    if num_personas <= 0:
        st.error("No hay personal para programar. Ajusta 'Total de personas actuales' o revisa requisitos.")
        st.stop()

    operadores = [f"{cargo} {i+1}" for i in range(num_personas)]

    # Construir lista de días (S1 y S2)
    dias_S1 = [f"{d} S1" for d in dias_disponibles]
    dias_S2 = [f"{d} S2" for d in dias_disponibles]
    columnas = dias_S1 + dias_S2

    # Inicializar DataFrame de programación con DESC por defecto
    df_prog = pd.DataFrame("DESC", index=operadores, columns=columnas)

    # Reglas por operador (cuotas a cumplir por semana)
    req_w1 = {}
    req_w2 = {}
    if esquema == "3x8":
        for op in operadores:
            req_w1[op] = {"8h": 6, "12h": 0}   # Semana 1: 6x8h
            req_w2[op] = {"8h": 3, "12h": 1}   # Semana 2: 3x8h + 1x12h
        # índice del día 12h en semana 2:
        dia_12h_idx = dias_disponibles.index(dia_12h_choice)
    else:  # 2x12
        for op in operadores:
            req_w1[op] = {"8h": 0, "12h": 4}   # Semana 1: 4x12h
            req_w2[op] = {"8h": 0, "12h": 3}   # Semana 2: 3x12h
        dia_12h_idx = None  # no aplica

    # Generar slots: cada elemento representa un turno que necesita 'min_operadores_turno' operadores
    slots = []
    # Semana 1
    for d_idx, d_name in enumerate(dias_disponibles):
        if esquema == "3x8":
            for t in range(n_turnos_dia_base):
                slots.append({"sem":1, "d_idx":d_idx, "d_name":d_name, "horas":8, "cupo":min_operadores_turno})
        else:
            for t in range(n_turnos_dia_base):
                slots.append({"sem":1, "d_idx":d_idx, "d_name":d_name, "horas":12, "cupo":min_operadores_turno})
    # Semana 2
    for d_idx, d_name in enumerate(dias_disponibles):
        if esquema == "3x8":
            if d_idx == dia_12h_idx:
                # Día especial: solo 2 turnos de 12h
                for t in range(2):
                    slots.append({"sem":2, "d_idx":d_idx, "d_name":d_name, "horas":12, "cupo":min_operadores_turno})
            else:
                for t in range(n_turnos_dia_base):
                    slots.append({"sem":2, "d_idx":d_idx, "d_name":d_name, "horas":8, "cupo":min_operadores_turno})
        else:
            for t in range(n_turnos_dia_base):
                slots.append({"sem":2, "d_idx":d_idx, "d_name":d_name, "horas":12, "cupo":min_operadores_turno})

    # Validación rápida por día: si num_personas < operadores necesarios por día, habrá faltantes
    faltantes = 0
    # Estructura para controlar asignaciones por día (evitar >1 turno por operador/día)
    asignaciones_por_dia = defaultdict(set)  # (sem, d_idx) -> set(operadores asignados ese día)
    # Deques para rotación (una sola cola global es suficiente para rotar)
    cola_global = deque(operadores)

    # Registros de asignaciones
    registros = []

    for slot_idx, slot in enumerate(slots):
        sem = slot["sem"]
        d_idx = slot["d_idx"]
        horas = slot["horas"]
        cupo = slot["cupo"]

        asignados_slot = []
        intentos = 0
        # Intentamos hasta 2 vueltas completas sobre la plantilla para no quedar en bucle infinito
        while len(asignados_slot) < cupo and intentos < len(operadores)*2:
            if not cola_global:
                cola_global = deque(operadores)
            op = cola_global[0]
            cola_global.rotate(-1)
            intentos += 1

            # Si ya fue asignado ese día -> no puede tomar otro turno ese mismo día
            if op in asignaciones_por_dia[(sem, d_idx)]:
                continue

            # Comprobar quota restante según semana
            req = req_w1[op] if sem == 1 else req_w2[op]
            if horas == 12 and req.get("12h", 0) > 0:
                # asignar 12h
                asignados_slot.append(op)
                asignaciones_por_dia[(sem, d_idx)].add(op)
                req["12h"] -= 1
                registros.append({"Semana":sem, "Día":slot["d_name"], "Día_col": f"{slot['d_name']} S{sem}", "Horas":12, "Operador":op})
            elif horas == 8 and req.get("8h", 0) > 0:
                # asignar 8h
                asignados_slot.append(op)
                asignaciones_por_dia[(sem, d_idx)].add(op)
                req["8h"] -= 1
                registros.append({"Semana":sem, "Día":slot["d_name"], "Día_col": f"{slot['d_name']} S{sem}", "Horas":8, "Operador":op})
            else:
                # si no tiene quota específica, se puede asignar si no quedan operadores con quota? 
                # (optamos por no forzar horas extra: seguimos buscando)
                continue

        if len(asignados_slot) < cupo:
            faltantes += (cupo - len(asignados_slot))

    # Llenar df_prog con asignaciones (si no asignado queda "DESC")
    for r in registros:
        op = r["Operador"]
        colname = r["Día_col"]
        if r["Horas"] == 12:
            df_prog.at[op, colname] = "12H"
        else:
            df_prog.at[op, colname] = "8H"

    # Mostrar DataFrame compacto (operadores filas, columnas días S1..S2)
    st.subheader("📅 Programación bi-semanal (filas = operadores, columnas = días S1/S2)")
    st.dataframe(df_prog, use_container_width=True)

    # Resumen de estado
    st.markdown("### Estado de la asignación")
    if faltantes > 0:
        st.warning(f"No se cubrieron {faltantes} posiciones de turno con el personal/criterios actuales (operadores insuficientes).")
    else:
        st.success("Se cubrieron todos los turnos según las cuotas definidas por operador.")

    # Ver si quedan cuotas pendientes por operador
    pendientes = []
    for op in operadores:
        pend_texts = []
        if req_w1[op].get("8h",0) > 0: pend_texts.append(f"Sem1: {req_w1[op]['8h']}x8h")
        if req_w1[op].get("12h",0) > 0: pend_texts.append(f"Sem1: {req_w1[op]['12h']}x12h")
        if req_w2[op].get("8h",0) > 0: pend_texts.append(f"Sem2: {req_w2[op]['8h']}x8h")
        if req_w2[op].get("12h",0) > 0: pend_texts.append(f"Sem2: {req_w2[op]['12h']}x12h")
        if pend_texts:
            pendientes.append((op, ", ".join(pend_texts)))
    if pendientes:
        st.info(f"Algunos operadores no completaron su cuota individual: {len(pendientes)} operador(es).")
        # Mostrar lista corta
        for op, texto in pendientes[:10]:
            st.write(f"- {op}: {texto}")
        if len(pendientes) > 10:
            st.write(f"... y {len(pendientes)-10} más.")
    else:
        st.write("Todos los operadores cumplieron sus cuotas individuales (según asignaciones realizadas).")

    # Descargar CSV y Excel
    csv_bytes = df_prog.to_csv(index=True).encode("utf-8")
    st.download_button("⬇️ Descargar programación (CSV)", data=csv_bytes, file_name="programacion_turnos.csv", mime="text/csv")

    # Excel (en memoria)
    try:
        import openpyxl
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_prog.to_excel(writer, sheet_name="Programacion", index=True)
            writer.save()
        st.download_button("⬇️ Descargar programación (XLSX)", data=buffer.getvalue(), file_name="programacion_turnos.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        st.info("No se pudo generar Excel (openpyxl no disponible). Puedes descargar el CSV.")

    # Nota final sobre reglas aplicadas
    if esquema == "3x8":
        st.caption("Regla aplicada 3x8: Semana1 = 6×8h, Semana2 = 3×8h + 1×12h (día 12H seleccionado). Un operador = máximo 1 turno/día.")
    else:
        st.caption("Regla aplicada 2x12: Semana1 = 4×12h, Semana2 = 3×12h. Un operador = máximo 1 turno/día.")
