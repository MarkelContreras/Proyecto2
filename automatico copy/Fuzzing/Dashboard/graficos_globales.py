# graficos_globales.py - clean and unified visual style (translated to English)
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import html
from Fuzzing.Dashboard.dashboard_utils import card, crear_grafico_bar, categorizar_longitud


def grafico_validos_vs_errores_global(df):
    valid_vs_errors = pd.DataFrame({
        "Type": ["Valid", "Errors"],
        "Count": [
            (df["fallo"] == False).sum(),
            (df["fallo"] == True).sum()
        ]
    })
    fig = crear_grafico_bar(valid_vs_errors, "Type", "Count", "Valid vs Errors count", color="Type", color_discrete_sequence=["#2ecc71", "#e74c3c"], show_legend=False)
    fig.update_layout(font_family='Arial', height=420, font=dict(size=16), margin=dict(t=60, l=40, r=40, b=120))
    fig.update_xaxes(tickfont=dict(size=16), tickangle=-30)
    fig.update_yaxes(tickfont=dict(size=16))
    return html.Div([card(fig, tipo='cuadrado')], style={"marginBottom": "30px"})

def grafico_codigos_error_global(df):
    errores_df = df[df["exit_code"] != 0]
    exit_counts = errores_df["exit_code"].value_counts().sort_index().reset_index()
    exit_counts.columns = ["Error code", "Frequency"]
    exit_counts["Error code"] = exit_counts["Error code"].astype(str)
    fig = crear_grafico_bar(exit_counts, "Error code", "Frequency", "Error code distribution", color="Error code", show_legend=False)
    fig.update_layout(height=420, font=dict(size=16), margin=dict(t=60, l=40, r=40, b=120))
    fig.update_xaxes(tickfont=dict(size=16))
    fig.update_yaxes(tickfont=dict(size=16))
    return html.Div([card(fig)], style={"marginBottom": "30px"})

def separador_horizontal_vertical():
    return html.Div(style={"height": "40px"})

def grafico_inputs_por_sesion(df):
    inputs_por_sesion = df.groupby("session_id")["input"].count().reset_index(name="total_inputs")
    fig = crear_grafico_bar(inputs_por_sesion, "session_id", "total_inputs", "Inputs per session", color="total_inputs", color_continuous_scale=px.colors.sequential.Cividis, show_legend=False)
    fig.update_layout(height=420, font=dict(size=16), margin=dict(t=60, l=40, r=40, b=120))
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=14))
    fig.update_yaxes(tickfont=dict(size=14))
    return card(fig)

def grafico_errores_por_sesion(df):
    errores_sesion = df[df["fallo"]].groupby("session_id")["exit_code"].count().reset_index(name="Errors")
    fig = crear_grafico_bar(errores_sesion, "session_id", "Errors", "Errors per session", color="Errors", color_continuous_scale=px.colors.sequential.Plasma, show_legend=False)
    fig.update_layout(height=420, font=dict(size=16), margin=dict(t=60, l=40, r=40, b=120))
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=14))
    fig.update_yaxes(tickfont=dict(size=16))
    return card(fig)

def grafico_duracion_sesiones(df):
    df = df[df["fecha_inicio"].notna() & df["fecha_fin"].notna() & df["hora_inicio"].notna() & df["hora_fin"].notna()]
    duraciones = []
    for sesion_id in df["session_id"].unique():
        sub_df = df[df["session_id"] == sesion_id].sort_values(by=["fecha_inicio", "hora_inicio"])
        try:
            dt_inicio = pd.to_datetime(f"{sub_df['fecha_inicio'].iloc[0]} {pd.Timestamp('00:00:00') + sub_df['hora_inicio'].iloc[0]:%H:%M:%S}")
            dt_fin = pd.to_datetime(f"{sub_df['fecha_fin'].iloc[-1]} {pd.Timestamp('00:00:00') + sub_df['hora_fin'].iloc[-1]:%H:%M:%S}")
            duraciones.append({"session_id": sesion_id, "duration_min": round((dt_fin - dt_inicio).total_seconds() / 60, 2)})
        except Exception as e:
            print(f"Error calculating duration for session {sesion_id}: {e}")
    df_duracion = pd.DataFrame(duraciones)
    fig = crear_grafico_bar(df_duracion, "session_id", "duration_min", "Session duration", color="duration_min", color_continuous_scale=px.colors.sequential.Tealgrn, show_legend=False)
    fig.update_layout(height=420, font=dict(size=16), margin=dict(t=60, l=40, r=40, b=120))
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=14))
    fig.update_yaxes(tickfont=dict(size=16))
    return card(fig)

def grafico_radar_programa():
    categorias = ['Metric 1', 'Metric 2', 'Metric 3', 'Metric 4', 'Metric 5']
    valores = [80, 70, 85, 75, 90]
    categorias_con_valores = [f"{cat}<br>{val}" for cat, val in zip(categorias, valores)]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=valores + [valores[0]], theta=categorias_con_valores + [categorias_con_valores[0]], fill='toself'))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=14))),
        showlegend=False,
        title={"text": "Program evaluation", "font": {"size": 22}},
        font=dict(size=18),
        margin=dict(t=80, l=60, r=60, b=80)
    )
    return card(fig)

def grafico_longitud_inputs_global(df, exito=True):
    fallo = df["fallo"]
    texto = "Valid input length" if exito else "Errored input length"
    colores = px.colors.sequential.Greens if exito else px.colors.sequential.Reds
    filtro = ~fallo if exito else fallo
    orden = ['0-50', '51-100', '101-300', '301-1000', '1000+']
    grupo = df[filtro].groupby("length_category").size().reset_index(name='Count')
    grupo["length_category"] = pd.Categorical(grupo["length_category"], categories=orden, ordered=True)
    fig = crear_grafico_bar(grupo.sort_values("length_category"), "length_category", "Count", texto, color="Count", color_continuous_scale=colores, show_legend=False)
    fig.update_layout(height=420, font=dict(size=16), margin=dict(t=60, l=40, r=40, b=120))
    fig.update_xaxes(tickfont=dict(size=16))
    fig.update_yaxes(tickfont=dict(size=16))
    return card(fig)

def grafico_ratio_fallos(df):
    resumen = (
        df.groupby("session_id")
        .agg(total_inputs=("input", "count"), errores=("exit_code", lambda x: (x != 0).sum()))
        .reset_index()
    )
    resumen["failure_ratio"] = resumen["errores"] / resumen["total_inputs"]

    fig = px.line(
        resumen,
        x="session_id",
        y="failure_ratio",
        title="Failure ratio per session",
        markers=True
    )
    fig.update_traces(line=dict(width=3), marker=dict(size=6))
    fig.update_layout(
        height=420,
        font=dict(size=16, family='Arial'),
        title={
            "text": "Failure ratio per session",
            "x": 0.5,
            "y": 0.9,
            "xanchor": "center",
            "yanchor": "top",
            "font": {"size": 18, "family": "Arial"}
        },
        margin=dict(t=60, l=40, r=40, b=120),
        yaxis_tickformat=".0%"
    )
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=14, family='Arial'))
    fig.update_yaxes(tickfont=dict(size=14), title="Failure ratio")

    return card(fig, tipo='cuadrado', categoria='ratio')
