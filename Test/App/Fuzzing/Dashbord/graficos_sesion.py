# graficos_sesion.py - clean and unified visual style
import pandas as pd
import plotly.express as px
from dash import html, dash_table, dcc
import math
from utils import card, crear_grafico_bar, categorizar_longitud

def grafico_errores_por_codigo(df):
    errores = df[df["exit_code"] != 0]["exit_code"].value_counts().sort_index().reset_index()
    errores.columns = ["Code", "Frequency"]
    errores["Code"] = errores["Code"].astype(str)
    fig = crear_grafico_bar(errores, "Code", "Frequency", "Error codes in session", color="Code")
    fig.update_layout(height=420, font=dict(size=16, family='Arial'), margin=dict(t=60, l=40, r=40, b=120))
    fig.update_xaxes(tickfont=dict(size=14))
    fig.update_yaxes(tickfont=dict(size=14))
    return html.Div([card(fig, tipo='cuadrado')], style={"marginBottom": "30px"})

def grafico_validos_vs_errores(df):
    conteo = pd.DataFrame({
        "Type": ["Valid", "Errors"],
        "Count": [
            (df["exit_code"] == 0).sum(),
            (df["exit_code"] != 0).sum()
        ]
    })
    fig = crear_grafico_bar(conteo, "Type", "Count", "Valid vs Errors in session", color="Type", color_discrete_sequence=["#2ecc71", "#e74c3c"], show_legend=False)
    fig.update_layout(height=420, font=dict(size=16, family='Arial'), margin=dict(t=60, l=40, r=40, b=120))
    fig.update_xaxes(tickfont=dict(size=14))
    fig.update_yaxes(tickfont=dict(size=14))
    return html.Div([card(fig, tipo='cuadrado')], style={"marginBottom": "30px"})

def grafico_longitud_histograma(df):
    fig = px.histogram(
        df,
        x="input_length",
        nbins=20,
        title="Input length distribution",
        labels={"input_length": "Input length"},
        color_discrete_sequence=["#636EFA"]
    )
    fig.update_layout(
        height=420,
        font=dict(size=16, family='Arial'),
        margin=dict(t=60, l=40, r=40, b=120),
        title={
            "text": "Input length distribution",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 18, "family": "Arial"}
        }
    )
    fig.update_traces(marker_line_width=1, marker_line_color="white")
    fig.update_xaxes(tickfont=dict(size=14))
    fig.update_yaxes(tickfont=dict(size=14))
    return html.Div([card(fig, tipo='cuadrado')], style={"marginBottom": "30px"})

def grafico_inputs_unicos_repetidos(df):
    conteos = df["input"].value_counts()
    unicos = (conteos == 1).sum()
    repetidos = (conteos > 1).sum()
    df_div = pd.DataFrame({"Type": ["Unique", "Repeated"], "Count": [unicos, repetidos]})
    fig = crear_grafico_bar(df_div, "Type", "Count", "Unique vs Repeated inputs", color="Type", color_discrete_sequence=["#3498db", "#e67e22"], show_legend=False)
    fig.update_layout(height=420, font=dict(size=16, family='Arial'), margin=dict(t=60, l=40, r=40, b=120))
    fig.update_xaxes(tickfont=dict(size=14))
    fig.update_yaxes(tickfont=dict(size=14))
    return html.Div([card(fig, tipo='cuadrado')], style={"marginBottom": "30px"})

def tabla_inputs_repetidos(df):
    conteos = df["input"].value_counts()
    repetidos = conteos[conteos > 1].reset_index()
    repetidos.columns = ["Input", "Count"]
    mitad = math.ceil(len(repetidos) / 2)
    tabla_1, tabla_2 = repetidos.iloc[:mitad], repetidos.iloc[mitad:]

    return html.Div([
        html.H4("Repeated inputs in session", style={"fontSize": "20px"}),
        dcc.Loading(
            id='loading-inputs-repeated',
            type="circle",
            color="#2c3e50",
            children=html.Div(style={"display": "flex", "gap": "30px"}, children=[
                dash_table.DataTable(
                    data=tabla_1.to_dict("records"),
                    columns=[{"name": col, "id": col} for col in tabla_1.columns],
                    style_table={"width": "100%", "tableLayout": "fixed", "overflowX": "auto"},
                    style_cell={"textAlign": "left", "padding": "10px", "fontSize": "16px"},
                    style_header={"backgroundColor": "#f9f9f9", "fontWeight": "bold", "fontSize": "17px"}
                ),
                dash_table.DataTable(
                    data=tabla_2.to_dict("records"),
                    columns=[{"name": col, "id": col} for col in tabla_2.columns],
                    style_table={"width": "100%", "tableLayout": "fixed", "overflowX": "auto"},
                    style_cell={"textAlign": "left", "padding": "10px", "fontSize": "16px"},
                    style_header={"backgroundColor": "#f9f9f9", "fontWeight": "bold", "fontSize": "17px"}
                )
            ])
        )
    ], style={"marginTop": "20px"})

def grafico_longitud_inputs(df, exito=True):
    texto = "Valid input length" if exito else "Errored input length"
    colores = px.colors.sequential.Greens if exito else px.colors.sequential.Reds
    filtro = df["exit_code"] == 0 if exito else df["exit_code"] != 0
    orden = ['0-50', '51-100', '101-300', '301-1000', '1000+']
    grupo = df[filtro].groupby("length_category").size().reset_index(name='Count')
    grupo["length_category"] = pd.Categorical(grupo["length_category"], categories=orden, ordered=True)
    fig = crear_grafico_bar(grupo.sort_values("length_category"), "length_category", "Count", texto, color="Count", color_continuous_scale=colores, show_legend=False)
    fig.update_layout(height=420, font=dict(size=16, family='Arial'), margin=dict(t=60, l=40, r=40, b=120))
    fig.update_xaxes(tickfont=dict(size=16))
    fig.update_yaxes(tickfont=dict(size=16))
    return html.Div([card(fig, tipo='cuadrado')], style={"marginBottom": "30px"})

def generar_graficos_sesion(df_base, programa, sesion):
    df_sesion = df_base[(df_base["programa"] == programa) & (df_base["session_id"] == sesion)].copy()
    df_sesion["exit_code"] = df_sesion["exit_code"].astype(int)
    df_sesion = df_sesion.drop_duplicates(subset=["input", "exit_code"])
    df_sesion["input_length"] = df_sesion["input"].apply(len)
    df_sesion["length_category"] = df_sesion["input_length"].apply(categorizar_longitud)

    return [
        grafico_errores_por_codigo(df_sesion),
        grafico_validos_vs_errores(df_sesion),
        grafico_longitud_histograma(df_sesion),
        grafico_inputs_unicos_repetidos(df_sesion),
        tabla_inputs_repetidos(df_sesion),
        grafico_longitud_inputs(df_sesion, exito=True),
        grafico_longitud_inputs(df_sesion, exito=False)
    ]
