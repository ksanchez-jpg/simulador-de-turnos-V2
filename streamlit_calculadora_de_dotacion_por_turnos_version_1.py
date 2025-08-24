import streamlit as st
import pandas as pd
import math
import json

st.set_page_config(
    page_title="CÁLCULO DE PERSONAL REQUERIDO",
    page_icon="🧮",
    layout="centered"
)
st.title("🧮 CÁLCULO DE PERSONAL REQUERIDO")
st.caption("Versión 1 – Cálculo mínimo de personal con base en horas requeridas, ausentismo y vacaciones.")

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
    """
)


# ---- Programación de Turnos ---- parte a cambiar y modificar
# ------------------------------
# Programación con descanso antes del cambio de turno
# ------------------------------
import streamlit as st
import pandas as pd
import math

st.subheader("📅 Programación mensual de turnos (rotación + descanso antes del cambio)")

# seguridad mínima: deben haber como mínimo min_operadores_turno por turno simultáneamente
if personal_total_requerido < num_turnos * min_operadores_turno:
    st.error(
        f"No hay suficiente personal para cubrir {num_turnos} turnos con {min_operadores_turno} operadores cada uno.\n"
        f"Se requieren al menos {num_turnos * min_operadores_turno} operadores en total."
    )
else:
    # === dividir operadores en grupos según turno inicial ===
    operadores = [f"OP{i+1}" for i in range(personal_total_requerido)]
    grupo_por_turno = {}
    base = personal_total_requerido // num_turnos
    resto = personal_total_requerido % num_turnos
    inicio = 0
    for t in range(1, num_turnos + 1):
        tam = base + (1 if t <= resto else 0)
        grupo_por_turno[t] = operadores[inicio: inicio + tam]
        inicio += tam

    # parametrización calendario
    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    num_semanas = 4

    # Inicializar estructura de schedule: schedule[op][col] = "Turno X" / "Descansa"
    cols = []
    for sem in range(1, num_semanas + 1):
        for d in dias_semana:
            cols.append(f"{d} - Semana {sem}")
    schedule = {op: {c: None for c in cols} for op in operadores}

    # Precompute turno de cada grupo por semana
    # group_id is the initial turno number (1..num_turnos)
    group_turno_week = {g: {} for g in grupo_por_turno.keys()}
    for g in grupo_por_turno.keys():
        for sem in range(1, num_semanas + 1):
            group_turno_week[g][sem] = ((g - 1 + (sem - 1)) % num_turnos) + 1

    # 1) Relleno por defecto: todos del grupo trabajan todos los días de la semana con el turno rotado
    for g, ops in grupo_por_turno.items():
        for sem in range(1, num_semanas + 1):
            turno_sem = group_turno_week[g][sem]
            for d in dias_semana:
                col = f"{d} - Semana {sem}"
                for op in ops:
                    schedule[op][col] = f"Turno {turno_sem}"

    # 2) Aplicar regla de descanso en los límites semana -> semana+1:
    #    para cada grupo, entre sem y sem+1 alternamos dentro del grupo
    #    quien descansa domingo y quien descansa lunes (de modo que nadie trabaje domingo+y lunes)
    for sem in range(1, num_semanas):  # boundary sem -> sem+1
        for g, ops in grupo_por_turno.items():
            # turno actual y siguiente (informativo)
            turno_actual = group_turno_week[g][sem]
            turno_siguiente = group_turno_week[g][sem + 1]

            # Si el turno cambia entre sem y sem+1 (normalmente cambia salvo num_turnos==1)
            if turno_actual != turno_siguiente:
                # patrón alternado: índices pares descansan domingo y empiezan lunes,
                # impares trabajan domingo y descansan lunes (arrancan martes)
                for i, op in enumerate(ops):
                    dom_col = f"Domingo - Semana {sem}"
                    lun_col = f"Lunes - Semana {sem + 1}"

                    if (i + sem) % 2 == 0:
                        # descansa el domingo, puede trabajar el lunes (comienza el nuevo turno el lunes)
                        schedule[op][dom_col] = "Descansa"
                        schedule[op][lun_col] = f"Turno {turno_siguiente}"
                    else:
                        # trabaja el domingo (último día en turno anterior), descansa el lunes (día de recuperación),
                        # comienza el nuevo turno el martes
                        schedule[op][dom_col] = f"Turno {turno_actual}"
                        schedule[op][lun_col] = "Descansa"
                # nota: otros días de la semana ya estaban marcados como "Turno X" por el rellenado por defecto

    # 3) Reparar cobertura mínima (greedy): para cada día y cada turno asegurar >= min_operadores_turno
    # construyo index para ver qué grupos están en qué turno ese día (usando group_turno_week)
    # función auxiliar para contar y obtener candidatos
    def count_workers_for_turn_day(week, day, turno_target):
        col = f"{day} - Semana {week}"
        workers = [op for op in operadores if schedule[op][col] == f"Turno {turno_target}"]
        return workers

    # Revisión por cada semana/día/turno
    for sem in range(1, num_semanas + 1):
        for d in dias_semana:
            col = f"{d} - Semana {sem}"
            for turno_target in range(1, num_turnos + 1):
                workers = count_workers_for_turn_day(sem, d, turno_target)
                if len(workers) >= min_operadores_turno:
                    continue  # ok

                # necesitamos más operadores: buscamos candidatos en los grupos cuyo turno esa semana == turno_target
                # candidatos deben estar "Descansa" en este col y no pueden haber trabajado el día anterior (para no violar la regla)
                candidates = []
                # compute previous day column (special for lunes)
                if d == "Lunes":
                    prev_col = f"Domingo - Semana {sem - 1}" if sem > 1 else None
                else:
                    # previous day in same week
                    idx = dias_semana.index(d)
                    prev_col = f"{dias_semana[idx - 1]} - Semana {sem}" if idx > 0 else None

                # collect groups whose assigned turno this week is turno_target
                groups_assigned = [g for g in grupo_por_turno.keys() if group_turno_week[g][sem] == turno_target]
                for g in groups_assigned:
                    for op in grupo_por_turno[g]:
                        if schedule[op][col] == "Descansa":
                            # ensure not working previous day (if prev_col exists)
                            if prev_col is None or not schedule[op][prev_col].startswith("Turno"):
                                candidates.append(op)

                # promote candidates until coverage satisfied
                promoted = []
                while len(workers) + len(promoted) < min_operadores_turno and candidates:
                    op = candidates.pop(0)
                    schedule[op][col] = f"Turno {turno_target}"
                    promoted.append(op)

                workers = count_workers_for_turn_day(sem, d, turno_target)
                if len(workers) < min_operadores_turno:
                    st.warning(
                        f"No se pudo cubrir completamente Turno {turno_target} el {d} - Semana {sem} "
                        f"respetando la regla 'descanso entre semanas'. Actualmente {len(workers)} / {min_operadores_turno}."
                    )

    # 4) Convertir a DataFrames y mostrar por grupo (tabla por turno-inicial)
    for g, ops in grupo_por_turno.items():
        st.write(f"### Grupo que inicia en Turno {g} (operadores: {len(ops)})")
        df = pd.DataFrame({f"{d} - Semana {s}": [schedule[op][f'{d} - Semana {s}'] for op in ops]
                           for s in range(1, num_semanas + 1) for d in dias_semana},
                          index=ops)
        df.index.name = "Operador"
        st.dataframe(df, use_container_width=True)
