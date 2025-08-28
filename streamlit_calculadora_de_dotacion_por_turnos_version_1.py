import streamlit as st
import pandas as pd
import math
from collections import defaultdict, deque

# -------------------- CONFIGURACIÓN DE LA APP --------------------
st.set_page_config(
    page_title="CÁLCULO DE PERSONAL REQUERIDO",
    page_icon="🧮",
    layout="centered"
)

st.title("🧮 CÁLCULO DE PERSONAL REQUERIDO Y PROGRAMACIÓN DE TURNOS")
st.caption("Versión 4 – Cálculo + programación bi-semanal con reglas operativas.")

# -------------------- ENTRADAS --------------------
col1, col2 = st.columns(2)

with col1:
    cargo = st.text_input("Nombre del cargo", value="Operador")
    ausentismo_pct = st.number_input("% de ausentismo", 0.0, 100.0, 8.0, step=0.5)
    horas_prom_bisem = st.number_input("Horas por semana (promedio bisemanal)", 10.0, 60.0, 42.0, step=0.5)
    personal_vacaciones = st.number_input("Personal de vacaciones esta quincena", min_value=0, value=0, step=1)

with col2:
    personas_actuales = st.number_input("Total de personas actuales en el cargo", min_value=0, value=0, step=1)
    dias_cubrir = st.number_input("Días a cubrir en la semana", 1, 7, 7, step=1)
    config_turnos = st.selectbox(
        "Configuración de turnos",
        ("3 turnos de 8 horas", "2 turnos de 12 horas"),
    )
    dias_vacaciones = st.number_input("Días de vacaciones por persona (esta quincena)", min_value=0, value=0, step=1)
    min_operadores_turno = st.number_input("Cantidad mínima de operadores por turno", 1, value=3, step=1)

# -------------------- CONFIGURACIÓN DE TURNOS --------------------
if "3 turnos" in config_turnos:
    n_turnos_dia_base, horas_por_turno = 3, 8
    esquema = "3x8"
else:
    n_turnos_dia_base, horas_por_turno = 2, 12
    esquema = "2x12"

# -------------------- CÁLCULOS DE DOTACIÓN --------------------
horas_semana_requeridas = dias_cubrir * n_turnos_dia_base * horas_por_turno * min_operadores_turno

factor_disponibilidad = 1.0 - (ausentismo_pct / 100.0)
if factor_disponibilidad <= 0:
    st.error("El % de ausentismo no puede ser 100% o más.")
    st.stop()

horas_semana_ajustadas = horas_semana_requeridas / factor_disponibilidad
personal_requerido_base = horas_semana_ajustadas / horas_prom_bisem

# Ajuste por vacaciones (usando carga promedio por día de la semana)
horas_dia_promedio = horas_prom_bisem / dias_cubrir
horas_vacaciones = personal_vacaciones * dias_vacaciones * horas_dia_promedio
personal_requerido_vacaciones = horas_vacaciones / horas_prom_bisem

personal_total_requerido = math.ceil(personal_requerido_base + personal_requerido_vacaciones)
brecha = personal_total_requerido - personas_actuales

# -------------------- RESULTADOS --------------------
st.subheader("📊 Resultados del cálculo")
col_res1, col_res2, col_res3 = st.columns(3)
col_res1.metric("Personal requerido (sin vacaciones)", f"{math.ceil(personal_requerido_base)}")
col_res2.metric("Personal adicional por vacaciones", f"{math.ceil(personal_requerido_vacaciones)}")
col_res3.metric("Total personal necesario", f"{personal_total_requerido}")
st.metric("Brecha frente al personal actual", f"{brecha:+}")

st.divider()
st.subheader("📅 Programación de turnos – 2 semanas")

# -------------------- SOPORTE: NOMBRES Y DÍAS --------------------
dias_nombre = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
dias_semana1 = dias_nombre[:dias_cubrir]
dias_semana2 = dias_nombre[:dias_cubrir]

# Número de personas a programar: usamos el disponible si lo hay; si es 0, usamos el requerido.
num_personas = personas_actuales if personas_actuales > 0 else personal_total_requerido
if num_personas <= 0:
    st.warning("No hay personal para programar. Ajusta 'Total de personas actuales' o revisa el cálculo requerido.")
    st.stop()

operadores = [f"{cargo} {i+1}" for i in range(num_personas)]

# -------------------- REGLAS INDIVIDUALES POR ESQUEMA --------------------
if esquema == "3x8":
    # Semana 1: 6 días de 8h (1 libre)
    # Semana 2: 3 días de 8h + 1 día de 12h
    req_w1 = {op: {"8h": 6, "12h": 0} for op in operadores}
    req_w2 = {op: {"8h": 3, "12h": 1} for op in operadores}
    # Día 12h en semana 2 (mitigar a 2 turnos): elegimos miércoles
    dia_12h_sem2_idx = 2  # 0=Lunes, 1=Martes, 2=Miércoles
else:
    # 2x12: Semana 1: 4x12h, Semana 2: 3x12h
    req_w1 = {op: {"8h": 0, "12h": 4} for op in operadores}
    req_w2 = {op: {"8h": 0, "12h": 3} for op in operadores}
    dia_12h_sem2_idx = None  # no aplica, todos los días son 12h

# -------------------- ESTRUCTURA DEL TABLERO DE SLOTS --------------------
def generar_slots_semana(semana, dias, esquema, n_turnos_base, min_ops, dia_12h_idx=None):
    """Genera slots (día, turno, horas) a cubrir para la semana."""
    slots = []  # cada slot: (semana, dia_idx, dia_nombre, turno_idx, horas)
    for d_idx, d_name in enumerate(dias):
        if esquema == "3x8":
            if semana == 2 and dia_12h_idx is not None and d_idx == dia_12h_idx:
                # Día mitigado: solo 2 turnos, ambos 12h
                for t in range(2):
                    slots.append( (semana, d_idx, d_name, t+1, 12, min_ops) )
            else:
                # Día normal: 3 turnos de 8h
                for t in range(n_turnos_base):
                    slots.append( (semana, d_idx, d_name, t+1, 8, min_ops) )
        else:  # 2x12
            for t in range(n_turnos_base):  # siempre 2 turnos
                slots.append( (semana, d_idx, d_name, t+1, 12, min_ops) )
    return slots

slots_w1 = generar_slots_semana(1, dias_semana1, esquema, n_turnos_dia_base, min_operadores_turno, None)
slots_w2 = generar_slots_semana(2, dias_semana2, esquema, n_turnos_dia_base, min_operadores_turno, dia_12h_sem2_idx)
slots = slots_w1 + slots_w2

# -------------------- PROGRAMADOR GREEDY BALANCEADO --------------------
# Control para asegurar: 1 turno máximo por operador/día.
asignaciones_por_dia = defaultdict(set)  # clave: (semana, dia_idx) -> set(operadores ya asignados ese día)
# Ruedas de reparto para balancear por turno:
colas_turno = defaultdict(lambda: deque(operadores))

def puede_asignar(op, semana, dia_idx, horas):
    # Validar que no esté ya asignado ese día
    if op in asignaciones_por_dia[(semana, dia_idx)]:
        return False
    # Validar que tenga disponibilidad según requerimientos individuales
    if semana == 1:
        req = req_w1[op]
    else:
        req = req_w2[op]
    if horas == 12 and req.get("12h", 0) > 0:
        return True
    if horas == 8 and req.get("8h", 0) > 0:
        return True
    return False

def registrar_asignacion(op, semana, dia_idx, horas):
    asignaciones_por_dia[(semana, dia_idx)].add(op)
    if semana == 1:
        if horas == 8 and req_w1[op]["8h"] > 0:
            req_w1[op]["8h"] -= 1
        elif horas == 12 and req_w1[op]["12h"] > 0:
            req_w1[op]["12h"] -= 1
    else:
        if horas == 8 and req_w2[op]["8h"] > 0:
            req_w2[op]["8h"] -= 1
        elif horas == 12 and req_w2[op]["12h"] > 0:
            req_w2[op]["12h"] -= 1

# Ejecutar asignación
asignaciones = []  # filas para el DataFrame final
faltantes = 0

for (sem, d_idx, d_name, turno, horas, cupo) in slots:
    cola = colas_turno[(sem, turno, horas)]
    # Rotar cola para no cargar siempre a los mismos
    intentos = 0
    asignados_este_slot = []
    while len(asignados_este_slot) < cupo and intentos < len(operadores) * 2:
        if not cola:
            cola = deque(operadores)
            colas_turno[(sem, turno, horas)] = cola
        op = cola[0]
        cola.rotate(-1)
        intentos += 1
        if puede_asignar(op, sem, d_idx, horas):
            registrar_asignacion(op, sem, d_idx, horas)
            asignados_este_slot.append(op)

    # Si no alcanzó el cupo, contamos faltantes
    if len(asignados_este_slot) < cupo:
        faltantes += (cupo - len(asignados_este_slot))

    # Registrar filas (siempre se crea el slot, aunque quede incompleto)
    for op in asignados_este_slot:
        asignaciones.append({
            "Semana": sem,
            "Día": d_name,
            "Turno": turno,
            "Horas": horas,
            "Operador": op
        })

# -------------------- VALIDACIONES Y AVISOS --------------------
# ¿Quedó alguien con requerimientos sin cumplir?
pendientes = []
if esquema == "3x8":
    for op in operadores:
        if req_w1[op]["8h"] > 0 or req_w2[op]["8h"] > 0 or req_w2[op]["12h"] > 0:
            pendientes.append(op)
else:
    for op in operadores:
        if req_w1[op]["12h"] > 0 or req_w2[op]["12h"] > 0:
            pendientes.append(op)

df_prog = pd.DataFrame(asignaciones)
if df_prog.empty:
    st.warning("No se pudo crear programación. Verifica que haya personal suficiente y parámetros coherentes.")
else:
    # Orden amigable: Semana, Día (según orden), Turno
    orden_dias = {n: i for i, n in enumerate(dias_nombre)}
    df_prog["Día_orden"] = df_prog["Día"].map(orden_dias)
    df_prog = df_prog.sort_values(by=["Semana","Día_orden","Turno","Operador"]).drop(columns=["Día_orden"])
    st.dataframe(df_prog, use_container_width=True)

    # Descarga
    csv = df_prog.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descargar programación (CSV)", data=csv, file_name="programacion_turnos_2_semanas.csv", mime="text/csv")

if faltantes > 0:
    st.warning(f"No se alcanzó a cubrir {faltantes} posiciones de turno con el personal/criterios actuales.")
if pendientes:
    st.info(f"Algunos operadores no completaron su meta individual de días/horas según el esquema: {len(pendientes)} operador(es). "
            "Puedes aumentar personal, reducir mínimos por turno o ajustar parámetros.")
    
# Nota visible para el usuario
if esquema == "3x8":
    st.caption("Criterio aplicado 3x8: Semana 1 (6×8h), Semana 2 (3×8h + 1×12h). Miércoles de la semana 2 se mitiga a 2 turnos.")
else:
    st.caption("Criterio aplicado 2x12: Semana 1 (4×12h), Semana 2 (3×12h). Rotación semanal de turno 1 → turno 2.")
