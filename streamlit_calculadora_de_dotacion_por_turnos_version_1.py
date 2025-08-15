import streamlit as st
import math

st.set_page_config(page_title="Cálculo de Personal", layout="wide")

# Título
st.title("📊 CÁLCULO DE PERSONAL REQUERIDO Y PROGRAMACIÓN DE TURNOS")
st.write("Versión 2 – Calcula el personal mínimo necesario para cubrir turnos sin horas extras, considerando ausentismo y vacaciones.")

# Panel lateral de explicación
with st.sidebar:
    st.header("¿Cómo funciona?")
    st.write("""
    Ingresas los parámetros operativos y la app estima el **número mínimo de personas**
    necesarias para cubrir los turnos de la semana, ajustado por ausentismo y vacaciones.
    
    **Fórmula base semanal**:
    - Horas requeridas = días por semana × turnos por día × mínimo de personas por turno × horas por turno
    - Personal requerido = horas requeridas ÷ horas/semana por persona
    - Ajuste por ausentismo = personal × (1 + % ausentismo)
    - Ajuste por vacaciones = horas totales de vacaciones ÷ horas/semana por persona
    """)
    st.info("La programación busca que no haya horas extras.")

# Entradas
col1, col2 = st.columns(2)

with col1:
    nombre_cargo = st.text_input("Nombre del cargo", "COSECHADOR")
    total_actual = st.number_input("Total de personas actuales en el cargo", min_value=0, value=19)
    ausentismo = st.number_input("% de ausentismo", min_value=0.0, value=6.27, step=0.01)
    horas_semana_persona = st.number_input("Horas por semana (promedio)", min_value=1.0, value=42.0)

with col2:
    dias_semana = st.number_input("Días a cubrir en la semana", min_value=1, max_value=7, value=7)
    horas_turno = st.selectbox("Configuración de turnos", [8, 10, 12], index=0)
    min_operadores_turno = st.number_input("Cantidad mínima de operadores por turno", min_value=1, value=6)
    personas_vacaciones = st.number_input("Personas de vacaciones", min_value=0, value=0)
    dias_vacaciones = st.number_input("Días de vacaciones", min_value=0, value=0)

# Cálculos
# Horas semanales base
turnos_por_dia = 24 / horas_turno
horas_semana_total = dias_semana * turnos_por_dia * min_operadores_turno * horas_turno

# Personal base
personal_base = horas_semana_total / horas_semana_persona

# Ajuste por ausentismo
personal_ajustado = personal_base * (1 + ausentismo / 100)

# Ajuste por vacaciones
horas_vacaciones_total = personas_vacaciones * dias_vacaciones * horas_turno
personal_vacaciones = horas_vacaciones_total / horas_semana_persona

# Personal total requerido
personal_total = personal_ajustado + personal_vacaciones

# Resultados
st.subheader("Resultados")
st.write(f"**Horas/semana a cubrir**: {horas_semana_total:.2f}")
st.write(f"**Personal requerido (base)**: {personal_base:.2f}")
st.write(f"**Personal ajustado por ausentismo**: {personal_ajustado:.2f}")
st.write(f"**Personal adicional por vacaciones**: {personal_vacaciones:.2f}")
st.write(f"### 👥 Personal total requerido: {math.ceil(personal_total)} personas")

# Mensaje sobre diferencia con personal actual
if total_actual >= personal_total:
    st.success("El personal actual es suficiente para cubrir los turnos sin horas extras.")
else:
    st.error(f"Se necesitan {math.ceil(personal_total - total_actual)} personas más para cubrir los turnos sin horas extras.")
