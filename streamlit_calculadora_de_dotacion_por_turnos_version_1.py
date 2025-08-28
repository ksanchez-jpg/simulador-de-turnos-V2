import streamlit as st
import pandas as pd
import math

# -------------------- CONFIGURACIÓN APP --------------------
st.set_page_config(
    page_title="CÁLCULO Y PROGRAMACIÓN DE TURNOS",
    page_icon="📋",
    layout="wide"
)

st.title("📋 CÁLCULO DE PERSONAL Y PROGRAMACIÓN DE TURNOS")
st.caption("Generador de programación automática de turnos en tablas separadas.")

# -------------------- ENTRADAS --------------------
col1, col2 = st.columns(2)

with col1:
    cargo = st.text_input("Nombre del cargo", value="Operador")
    ausentismo_pct = st.number_input("% de ausentismo", 0.0, 100.0, 8.0, step=0.5)
    horas_prom_bisem = st.number_input("Horas por semana (promedio bisemanal)", 10.0, 60.0, 42.0, step=0.5)
    personal_vacaciones = st.number_input("Personal de vacaciones", min_value=0, value=0, step=1)

with col2:
    personas_actuales = st.number_input("Total de personas actuales en el cargo", min_value=0, value=6, step=1)
    dias_cubrir = st.number_input("Días a cubrir en la semana", 1, 7, 7, step=1)
    config_turnos = st.selectbox("Configuración de turnos", ("3 turnos de 8 horas", "2 turnos de 12 horas"))
    dias_vacaciones = st.number_input("Días de vacaciones", min_value=0, value=0, step=1)
    min_operadores_turno = st.number_input("Cantidad mínima de operadores por turno", 1, value=3, step=1)

# -------------------- CONFIGURACIÓN DE TURNOS --------------------
if "3 turnos" in config_turnos:
    n_turnos_dia, horas_por_turno = 3, 8
else:
    n_turnos_dia, horas_por_turno = 2, 12

# -------------------- CÁLCULO DE PERSONAL --------------------
horas_semana_requeridas = dias_cubrir * n_turnos_dia * horas_por_turno * min_operadores_turno
factor_disponibilidad = 1.0 - (ausentismo_pct / 100.0)

if factor_disponibilidad <= 0:
    st.error("El % de ausentismo no puede ser 100% o más.")
    st.stop()

horas_semana_ajustadas = horas_semana_requeridas / factor_disponibilidad
personal_requerido_base = horas_semana_ajustadas / horas_prom_bisem

# Ajuste por vacaciones
horas_vacaciones = personal_vacaciones * dias_vacaciones * horas_por_turno
personal_requerido_vacaciones = horas_vacaciones / horas_prom_bisem

# Total requerido
personal_total_requerido = math.ceil(personal_requerido_base + personal_requerido_vacaciones)
brecha = personal_total_requerido - personas_actuales

# -------------------- RESULTADOS --------------------
st.subheader("📊 Resultados")
st.metric("Personal total necesario", f"{personal_total_requerido}")
st.metric("Brecha de personal (faltante)", f"{brecha}")

st.divider()


# -------------------- PROGRAMACIÓN DE TURNOS --------------------
import pandas as pd
import random
import streamlit as st

# Parámetros (puedes conectar esto con tu cálculo de personal)
num_operadores = 9  # ejemplo
turnos = 3
dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# Función para generar programación rotativa
def generar_programacion(num_operadores, turnos, horas_turno="8h"):
    operadores = [f"Op{i+1}" for i in range(num_operadores)]
    random.shuffle(operadores)  # Para que no siempre descansen los mismos
    
    # Dividir operadores en turnos
    operadores_turnos = [operadores[i::turnos] for i in range(turnos)]
    
    tablas = {}
    for t, ops in enumerate(operadores_turnos, start=1):
        data = {"Operador": ops}
        
        # Semana 1 y Semana 2
        for semana in [1, 2]:
            for dia in dias_semana:
                col = f"{dia} Sem{semana}"
                valores = []
                for op in ops:
                    if horas_turno == "8h":
                        if semana == 1:
                            valores.append("8H") if random.random() > 0.15 else valores.append("Descanso")
                        else:
                            # Rotación: 3 días 8h + 1 día 12h
                            if random.random() < 0.15:
                                valores.append("12H")
                            elif random.random() < 0.7:
                                valores.append("8H")
                            else:
                                valores.append("Descanso")
                    elif horas_turno == "12h":
                        if semana == 1:
                            valores.append("12H") if random.random() > 0.35 else valores.append("Descanso")
                        else:
                            valores.append("12H") if random.random() > 0.45 else valores.append("Descanso")
                data[col] = valores
        
        tablas[f"Turno {t}"] = pd.DataFrame(data)
    
    return tablas

# Streamlit UI
st.title("📅 Programación de Turnos")

tipo_turno = st.radio("Selecciona el tipo de turno:", ["8h", "12h"])

tablas = generar_programacion(num_operadores, turnos, horas_turno=tipo_turno)

# Mostrar cada turno en tablas separadas
for turno, tabla in tablas.items():
    st.subheader(turno)
    st.dataframe(tabla, use_container_width=True)

