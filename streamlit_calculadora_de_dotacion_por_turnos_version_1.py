import math
import streamlit as st
import json
import pandas as pd
import numpy as np
import io

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
    - La V2 generará calendario de 4 semanas que cumpla las restricciones de descansos y rotación.
    """
)

# =========================================================================
# ---- Sección de funcionalidad adicional: Programación de Turnos (V2) ----
# =========================================================================

st.divider()
st.header("🗓️ Programación de Turnos (Versión V2)")
st.info("Esta es una programación de 4 semanas que considera la rotación de turnos, días de descanso y personal adicional.")

# Definimos los días de la semana y los turnos
dias_de_la_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
turnos = [f"Turno {i+1}" for i in range(n_turnos_dia)]

# Creamos las listas de operadores actuales y adicionales
personal_actual = [f"OP{i+1}" for i in range(personal_total_requerido)]
num_adicional = math.ceil(personal_total_requerido * (2/5))
personal_adicional = [f"OP-AD{i+1}" for i in range(num_adicional)]
personal_total = personal_actual + personal_adicional

# Creamos un DataFrame para la programación completa
columnas = [f"{dias_de_la_semana[i % 7]} (Semana {i // 7 + 1})" for i in range(28)]
programacion_df = pd.DataFrame(index=personal_total, columns=columnas)
programacion_df.fillna("", inplace=True)

# Lógica de programación de turnos y descansos
if n_turnos_dia > 0:
    for i, operador in enumerate(personal_actual):
        # Asignamos un patrón de 5 días de trabajo y 2 de descanso, rotativo
        dias_trabajo = 5
        dias_descanso = 2
        
        # El turno de inicio y el día de descanso se escalonan para cada operador
        turno_inicio_idx = i % n_turnos_dia
        dia_descanso_inicio_idx = (i * (dias_trabajo + dias_descanso)) % 7

        for semana in range(4):
            # Asignamos el turno de la semana
            turno_asignado = turnos[(turno_inicio_idx + semana) % n_turnos_dia]
            
            # Calculamos los días de descanso para la semana actual
            descanso_semana_inicio = (dia_descanso_inicio_idx + semana) % 7
            dias_descanso_semana = [(descanso_semana_inicio + j) % 7 for j in range(dias_descanso)]
            
            for dia_idx, dia_nombre in enumerate(dias_de_la_semana):
                col_name = f"{dia_nombre} (Semana {semana+1})"

                if dia_idx in dias_descanso_semana:
                    programacion_df.loc[operador, col_name] = "Descansa"
                else:
                    programacion_df.loc[operador, col_name] = turno_asignado

# Lógica para los operadores adicionales
if n_turnos_dia > 0:
    for i, op_adicional in enumerate(personal_adicional):
        # Patrón de trabajo de los operadores adicionales
        dias_trabajo = 5
        dias_descanso = 2
        
        turno_inicio_idx = i % n_turnos_dia
        dia_descanso_inicio_idx = (i * (dias_trabajo + dias_descanso) + 3) % 7 # Patrón de descanso diferente

        for semana in range(4):
            turno_asignado = turnos[(turno_inicio_idx + semana) % n_turnos_dia]
            dias_descanso_semana = [(dia_descanso_inicio_idx + j) % 7 for j in range(dias_descanso)]
            
            for dia_idx, dia_nombre in enumerate(dias_de_la_semana):
                col_name = f"{dia_nombre} (Semana {semana+1})"
                
                if dia_idx in dias_descanso_semana:
                    programacion_df.loc[op_adicional, col_name] = "Descansa"
                else:
                    programacion_df.loc[op_adicional, col_name] = turno_asignado

# Lógica de reemplazo de los operadores que descansan
for dia_col in columnas:
    for op_actual in personal_actual:
        if programacion_df.loc[op_actual, dia_col] == "Descansa":
            semana = int(dia_col.split("Semana ")[1].replace(")", "")) - 1
            dia_idx = dias_de_la_semana.index(dia_col.split(" (Semana")[0])
            
            # Buscar un operador adicional disponible
            for op_adicional in personal_adicional:
                if programacion_df.loc[op_adicional, dia_col] != "Descansa":
                    programacion_df.loc[op_adicional, dia_col] = f"Cubre {op_actual}"
                    break

# Creamos las tablas finales para cada turno
programacion_por_turno_final = {turno: pd.DataFrame(index=[], columns=columnas) for turno in turnos}

for operador in personal_total:
    primer_turno_asignado = ""
    for dia_col in columnas:
        if "Turno" in programacion_df.loc[operador, dia_col]:
            primer_turno_asignado = programacion_df.loc[operador, dia_col]
            break
    
    if not primer_turno_asignado and operador in personal_adicional:
        # En el caso de los operadores adicionales que solo cubren, su turno "base" no es relevante
        # Los agregamos a todas las tablas para que su rol de "Cubre" sea visible
        for turno in turnos:
            programacion_por_turno_final[turno].loc[operador] = ""
    
    elif primer_turno_asignado:
        # Añadir al operador a la tabla de su turno base
        programacion_por_turno_final[primer_turno_asignado].loc[operador] = ""

        # Llenamos la programación para los 28 días
        for dia_col in columnas:
            valor = programacion_df.loc[operador, dia_col]
            
            if valor.startswith("Turno"):
                programacion_por_turno_final[valor].loc[operador, dia_col] = "Trabaja"
            elif valor == "Descansa":
                programacion_por_turno_final[primer_turno_asignado].loc[operador, dia_col] = "Descansa"
            elif valor.startswith("Cubre"):
                turno_cubierto = valor.split("Cubre ")[1]
                # Esta parte necesita una corrección. Ahora solo necesitamos saber si está cubriendo
                programacion_por_turno_final[turno_cubierto].loc[operador, dia_col] = "Cubre"


# Nuevo enfoque de visualización para evitar filas vacías
for turno, df in programacion_por_turno_final.items():
    filas_a_mostrar = []
    for operador in df.index:
        if df.loc[operador].any():
            filas_a_mostrar.append(operador)
    
    if filas_a_mostrar:
        df_limpio = df.loc[filas_a_mostrar]
        st.subheader(f"Programación {turno}")
        st.dataframe(df_limpio)
        
# ---- Descargar Excel ----
@st.cache_data
def convert_df_to_excel(df_dict):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for sheet_name, df in df_dict.items():
            df.to_excel(writer, sheet_name=sheet_name)
    processed_data = output.getvalue()
    return processed_data

excel_data = convert_df_to_excel(programacion_por_turno_final)

st.download_button(
    label="⬇️ Descargar Programación (Excel)",
    data=excel_data,
    file_name='programacion_turnos.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)
