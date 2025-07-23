# DashBoard/Dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px
import time
import os
import plotly.colors


st.set_page_config(page_title="Fuzzing Dashboard", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_PARQUET = os.path.join(BASE_DIR, "Parquet")


# ---------------------
# Funciones de carga
# ---------------------
@st.cache_data
def listar_programas():
    carpetas = [f.name for f in os.scandir(BASE_PARQUET) if f.is_dir()]
    return sorted(carpetas)

@st.cache_data
def cargar_datos_ligeros(programa):
    ruta = os.path.join(BASE_PARQUET, programa, "resumen_fuzzing_ligero.parquet")
    return pd.read_parquet(ruta)

@st.cache_data
def cargar_inputs(programa):
    ruta = os.path.join(BASE_PARQUET, programa, "fuzzing_inputs.parquet")
    return pd.read_parquet(ruta)

# ---------------------
# Funciones de gráficos
# ---------------------
def graficar_inputs_por_sesion(df):
    df_inputs = df.groupby("session_id")["id"].count().reset_index(name="total_inputs")
    fig = px.bar(df_inputs, x="session_id", y="total_inputs", title="📦 Inputs por sesión")
    return fig

def graficar_errores_por_sesion(df):
    errores = df[df["exit_code"] != 0].groupby("session_id")["exit_code"].count().reset_index(name="errores")
    fig = px.bar(
        errores,
        x="session_id",
        y="errores",
        title="❌ Errores por sesión",
        color_discrete_sequence=["#e74c3c"]  # Rojo intenso
    )
    fig.update_layout(
        xaxis_title="Sesión",
        yaxis_title="Cantidad de errores"
    )
    return fig


def graficar_ratio_fallos(df):
    resumen = (
        df.groupby("session_id")
        .agg(total_inputs=("id", "count"), errores=("exit_code", lambda x: (x != 0).sum()))
        .reset_index()
    )
    resumen["ratio_fallo"] = resumen["errores"] / resumen["total_inputs"]
    fig = px.line(resumen, x="session_id", y="ratio_fallo", title="📉 Ratio de fallos por sesión", markers=True)
    fig.update_yaxes(tickformat=".0%")
    return fig

def graficar_duracion(df):
    if not all(col in df.columns for col in ["fecha_inicio", "fecha_fin", "hora_inicio", "hora_fin"]):
        return None

    df_clean = df.dropna(subset=["fecha_inicio", "fecha_fin", "hora_inicio", "hora_fin"])
    duraciones = []
    for sid in df_clean["session_id"].unique():
        sub = df_clean[df_clean["session_id"] == sid]
        try:
            t_ini = pd.to_datetime(sub["fecha_inicio"].iloc[0].strftime("%Y-%m-%d") + " " + str(sub["hora_inicio"].iloc[0]))
            t_fin = pd.to_datetime(sub["fecha_fin"].iloc[-1].strftime("%Y-%m-%d") + " " + str(sub["hora_fin"].iloc[-1]))
            duracion = round((t_fin - t_ini).total_seconds() / 60, 2)
            duraciones.append({"session_id": sid, "duracion_min": duracion})
        except:
            continue

    if not duraciones:
        return None

    df_duracion = pd.DataFrame(duraciones)
    fig = px.bar(df_duracion, x="session_id", y="duracion_min", title="⏱️ Duración por sesión (min)")
    return fig

def graficar_longitudes_inputs(df_inputs):
    df_inputs["input_len"] = df_inputs["input"].apply(lambda x: len(x) if pd.notnull(x) else 0)

    bins = [0, 50, 100, 300, 1000, float("inf")]
    labels = ['0-50', '51-100', '101-300', '301-1000', '1000+']
    df_inputs["rango_longitud"] = pd.cut(df_inputs["input_len"], bins=bins, labels=labels, right=True)

    resumen = df_inputs["rango_longitud"].value_counts().reindex(labels, fill_value=0).reset_index()
    resumen.columns = ["Rango", "Cantidad"]

    fig = px.bar(
        resumen,
        x="Rango",
        y="Cantidad",
        title="📏 Distribución de longitudes de inputs",
        color="Rango",
        color_discrete_sequence=px.colors.sequential.Reds
    )
    fig.update_layout(
        xaxis_title="Longitud del input",
        yaxis_title="Número de inputs",
        showlegend=False
    )
    return fig

def graficar_validos_vs_invalidos(df):
    df["valido"] = df["exit_code"] == 0
    resumen = (
        df.groupby(["session_id", "valido"])
        .size()
        .reset_index(name="count")
        .replace({True: "Valid", False: "Invalid"})
    )

    fig = px.bar(
        resumen,
        x="session_id",
        y="count",
        color="valido",
        title="✔️ Válidos vs ❌ Inválidos por sesión",
        labels={"count": "Número de inputs", "valido": "Tipo de input"},
        barmode="group",
        color_discrete_map={"Valid": "#2ecc71", "Invalid": "#e74c3c"}
    )

    fig.update_layout(xaxis_title="Session ID", yaxis_title="Número de inputs")
    return fig

def graficar_duracion_sesiones(df):
    if not all(col in df.columns for col in ["fecha_inicio", "fecha_fin", "hora_inicio", "hora_fin"]):
        st.warning("⚠️ Faltan columnas necesarias para calcular la duración.")
        return None

    df_clean = df.dropna(subset=["fecha_inicio", "fecha_fin", "hora_inicio", "hora_fin"])
    duraciones = []

    for sid in df_clean["session_id"].unique():
        sub = df_clean[df_clean["session_id"] == sid]
        try:
            fecha_ini = str(sub["fecha_inicio"].iloc[0])
            hora_ini_raw = str(sub["hora_inicio"].iloc[0])
            hora_ini = hora_ini_raw.strip().split()[-1]  # extrae '09:00:00' de '0 days 09:00:00'

            fecha_fin = str(sub["fecha_fin"].iloc[-1])
            hora_fin_raw = str(sub["hora_fin"].iloc[-1])
            hora_fin = hora_fin_raw.strip().split()[-1]

            t_ini = pd.to_datetime(f"{fecha_ini} {hora_ini}")
            t_fin = pd.to_datetime(f"{fecha_fin} {hora_fin}")

            duracion = round((t_fin - t_ini).total_seconds() / 60, 2)
            duraciones.append({"session_id": sid, "duracion_min": duracion})
        except Exception as e:
            st.warning(f"⚠️ Error en sesión {sid}: {e}")
            continue

    if not duraciones:
        st.warning("⚠️ No se pudieron calcular duraciones válidas.")
        return None

    df_duracion = pd.DataFrame(duraciones)
    fig = px.bar(
        df_duracion,
        x="session_id",
        y="duracion_min",
        title="⏱️ Duración de las sesiones (en minutos)",
        labels={"duracion_min": "Duración (min)", "session_id": "Sesión"},
        color="duracion_min",
        color_continuous_scale="blues"
    )
    return fig


def graficar_codigos_error_individuales(df):
    errores = df[df["exit_code"] != 0]
    if errores.empty:
        st.info("ℹ️ No hay errores registrados para mostrar.")
        return None

    conteo = (
        errores.groupby(["session_id", "exit_code"])
        .size()
        .reset_index(name="count")
    )

    conteo["exit_code"] = conteo["exit_code"].astype(str)
    codigos = sorted(conteo["exit_code"].unique())

    st.subheader("📊 Códigos de error por sesión")
    
    for code in codigos:
        sub_df = conteo[conteo["exit_code"] == code]
        fig = px.bar(
            sub_df,
            x="session_id",
            y="count",
            title=f"🧯 Código de error {code}",
            labels={"count": "Número de errores", "session_id": "Sesión"},
            color_discrete_sequence=["#e74c3c"] 
        )
        fig.update_layout(
            xaxis_title="Sesión",
            yaxis_title="Errores del código",
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)





# ---------------------
# Interfaz principal
# ---------------------
st.title("Dashboard Fuzzing")

with st.spinner("🔍 Buscando programas disponibles..."):
    programas = listar_programas()

if not programas:
    st.error("❌ No se encontraron programas en la carpeta 'Parquet'.")
    st.stop()

programa_sel = st.selectbox("Selecciona un programa", programas)

with st.spinner(f"Cargando datos ligeros de '{programa_sel}'..."):
    df_ligero = cargar_datos_ligeros(programa_sel)

st.plotly_chart(graficar_inputs_por_sesion(df_ligero), use_container_width=True)
st.plotly_chart(graficar_errores_por_sesion(df_ligero), use_container_width=True)
st.plotly_chart(graficar_ratio_fallos(df_ligero), use_container_width=True)
st.plotly_chart(graficar_validos_vs_invalidos(df_ligero), use_container_width=True)

fig_codigos = graficar_codigos_error_individuales(df_ligero)

if fig_codigos:
    st.plotly_chart(fig_codigos, use_container_width=True)


df_duraciones = None
fig_duracion = graficar_duracion_sesiones(df_ligero)
if fig_duracion:
    st.plotly_chart(fig_duracion, use_container_width=True)


# ---------------------
# Carga de inputs pesados
# ---------------------

with st.spinner("Cargando inputs completos..."):
    try:
        t_ini = time.time()
        df_inputs = cargar_inputs(programa_sel)
        fig_inputs = graficar_longitudes_inputs(df_inputs)
        st.plotly_chart(fig_inputs, use_container_width=True)
        st.success(f"✅ Inputs cargados en {round(time.time() - t_ini, 2)} segundos")
    except Exception as e:
        st.warning(f"No se pudieron cargar los inputs: {e}")