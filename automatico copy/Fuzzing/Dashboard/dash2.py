# dash2.py - updated with collapsibles and improved styles
import pandas as pd
import time
import sys

import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from Fuzzing.Dashboard.graficos_sesion import (
    generar_graficos_sesion,
    grafico_errores_por_codigo,
    grafico_validos_vs_errores,
    grafico_longitud_histograma,
    grafico_inputs_unicos_repetidos,
    tabla_inputs_repetidos,
    grafico_longitud_inputs,
    categorizar_longitud
)
from Fuzzing.Dashboard.graficos_globales import (
    grafico_validos_vs_errores_global,
    grafico_codigos_error_global,
    grafico_inputs_por_sesion,
    grafico_errores_por_sesion,
    grafico_duracion_sesiones,
    grafico_radar_programa,
    grafico_longitud_inputs_global,
    categorizar_longitud,
    grafico_ratio_fallos
)
from utils.config_db import get_connection



conn = get_connection()
if conn is None:
    print("Connection to the database failed.")
    sys.exit(1)

query = "SELECT * FROM fuzzing"
df = pd.read_sql(query, conn)
conn.close()

def generar_graficos(df_base, programa=None, sesion=None):
    if not programa:
        return [], []

    df_global_full = df_base[df_base["programa"] == programa].copy()
    df_global_full["exit_code"] = df_global_full["exit_code"].astype(int)
    df_global_full["fallo"] = df_global_full["exit_code"] != 0

    df_global = df_global_full.drop_duplicates(subset=["input", "exit_code"])
    df_global["input_length"] = df_global["input"].apply(len)
    df_global["length_category"] = df_global["input_length"].apply(categorizar_longitud)

    global_cards = [
        grafico_inputs_por_sesion(df_global_full),
        grafico_validos_vs_errores_global(df_global),
        grafico_codigos_error_global(df_global),
        grafico_errores_por_sesion(df_global_full),
        grafico_duracion_sesiones(df_global_full),
        # grafico_radar_programa(),
        grafico_longitud_inputs_global(df_global, exito=True),
        grafico_longitud_inputs_global(df_global, exito=False),
        grafico_ratio_fallos(df_global_full)
    ]

    if not sesion:
        return global_cards, []

    df_sesion = df_base[(df_base["programa"] == programa) & (df_base["session_id"] == sesion)].copy()
    df_sesion["exit_code"] = df_sesion["exit_code"].astype(int)
    df_sesion_original = df_sesion.copy()
    df_sesion = df_sesion.drop_duplicates(subset=["input", "exit_code"])

    for df_ in (df_sesion, df_sesion_original):
        df_["input_length"] = df_["input"].apply(len)
        df_["length_category"] = df_["input_length"].apply(categorizar_longitud)

    session_cards = [
        grafico_errores_por_codigo(df_sesion),
        grafico_validos_vs_errores(df_sesion),
        grafico_longitud_histograma(df_sesion),
        grafico_inputs_unicos_repetidos(df_sesion_original),
        grafico_longitud_inputs(df_sesion, exito=True),
        grafico_longitud_inputs(df_sesion, exito=False)
    ]

    return global_cards, session_cards

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Fuzzing Dashboard"
programas_unicos = sorted(df["programa"].unique())

app.layout = html.Div(style={"backgroundColor": "#f9f9f9", "padding": "20px", "fontFamily": "Arial, sans-serif"}, children=[
    html.H1("Fuzzing Dashboard", style={"textAlign": "center", "color": "#333"}),

    html.Div(style={"display": "flex", "justifyContent": "center", "marginBottom": "40px"}, children=[
        html.Div(style={"backgroundColor": "#ffffff", "padding": "30px", "borderRadius": "15px", "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.1)", "maxWidth": "1400px", "width": "100%"}, children=[
            html.H2("Filter results", style={"textAlign": "center", "marginBottom": "25px", "color": "#333"}),
            html.Div(style={"display": "flex", "justifyContent": "space-between", "gap": "20px"}, children=[
                html.Div(style={"flex": "1"}, children=[
                    html.Label("Program", style={"fontWeight": "bold"}),
                    dcc.Dropdown(id="programa-dropdown", options=[{"label": p, "value": p} for p in programas_unicos], placeholder="Select a program")
                ]),
                html.Div(style={"flex": "1"}, children=[
                    html.Label("Session", style={"fontWeight": "bold"}),
                    dcc.Dropdown(id="sesion-dropdown", placeholder="Select a session")
                ])
            ])
        ])
    ]),

    html.Div(children=[
        html.H3(id="titulo-global", children="➖ Global Program Analysis", style={"fontSize": "22px", "color": "#333", "marginBottom": "15px", "cursor": "pointer"}),
        dbc.Collapse(
            id="collapse-global",
            is_open=True,
            style={"backgroundColor": "transparent", "padding": "0px", "margin": "0px"},
            children=dcc.Loading(
                type="circle",
                color="#2c3e50",
                children=html.Div(id="bloque-global-content", style={"backgroundColor": "transparent"})
            )
        )
    ]),

    html.Div(children=[
        html.H3(id="titulo-sesiones", children="➖ Detailed Session Analysis", style={"fontSize": "22px", "color": "#333", "marginBottom": "15px", "cursor": "pointer"}),
        dbc.Collapse(
            id="collapse-sesiones",
            is_open=True,
            style={"backgroundColor": "transparent", "padding": "0px", "margin": "0px"},
            children=dcc.Loading(
                type="circle",
                color="#2c3e50",
                children=html.Div(id="bloque-sesiones-content", style={"backgroundColor": "transparent"})
            )
        )
    ])
])

@app.callback(
    Output("sesion-dropdown", "options"),
    Output("sesion-dropdown", "value"),
    Input("programa-dropdown", "value")
)
def actualizar_sesiones(programa_seleccionado):
    if programa_seleccionado is None:
        return [], None
    sesiones = df[df["programa"] == programa_seleccionado]["session_id"].unique()
    return [{"label": s, "value": s} for s in sorted(sesiones)], None

@app.callback(
    Output("collapse-global", "is_open"),
    Output("titulo-global", "children"),
    Input("titulo-global", "n_clicks"),
    State("collapse-global", "is_open")
)
def toggle_global(n, is_open):
    if n:
        nuevo_estado = not is_open
    else:
        nuevo_estado = is_open
    icono = "➖" if nuevo_estado else "➕"
    return nuevo_estado, f"{icono} Global Program Analysis"

@app.callback(
    Output("collapse-sesiones", "is_open"),
    Output("titulo-sesiones", "children"),
    Input("titulo-sesiones", "n_clicks"),
    State("collapse-sesiones", "is_open")
)
def toggle_sesiones(n, is_open):
    if n:
        nuevo_estado = not is_open
    else:
        nuevo_estado = is_open
    icono = "➖" if nuevo_estado else "➕"
    return nuevo_estado, f"{icono} Detailed Session Analysis"

@app.callback(
    Output("bloque-global-content", "children"),
    Input("programa-dropdown", "value"),
    prevent_initial_call=True
)
def actualizar_global(programa):
    if not programa:
        return html.P("Select a program to view its analysis.", style={"textAlign": "center", "fontSize": "18px"})
    time.sleep(1)
    global_cards, _ = generar_graficos(df, programa=programa, sesion=None)

    graficos_session_id = []
    graficos_otros = []
    for card in global_cards:
        if "session_id" in str(card).lower():
            graficos_session_id.append(card)
        else:
            graficos_otros.append(card)

    return html.Div([
        html.Div(graficos_session_id, style={
            "display": "grid",
            "gridTemplateColumns": "repeat(auto-fit, minmax(500px, 1fr))",
            "gap": "30px 40px",
            "width": "100%"
        }),

        html.Hr(style={
            "margin": "50px 0",
            "border": "none"
        }),

        html.Div(graficos_otros, style={
            "display": "grid",
            "gap": "30px 40px",
            "gridTemplateColumns": "repeat(auto-fit, minmax(300px, 1fr))",
            "alignItems": "start",
            "width": "100%"
        })
    ])

@app.callback(
    Output("bloque-sesiones-content", "children"),
    Input("programa-dropdown", "value"),
    Input("sesion-dropdown", "value"),
    prevent_initial_call=True
)
def actualizar_sesion(programa, sesion):
    if not programa or not sesion:
        return []
    time.sleep(1)
    _, session_cards = generar_graficos(df, programa=programa, sesion=sesion)

    graficos_session_id = []
    graficos_otros = []
    for card in session_cards:
        if "session_id" in str(card).lower():
            graficos_session_id.append(card)
        else:
            graficos_otros.append(card)

    return html.Div([
        html.Div(graficos_session_id, style={
            "display": "grid",
            "gridTemplateColumns": "repeat(auto-fit, minmax(500px, 1fr))",
            "gap": "30px 40px",
            "width": "100%"
        }),

        html.Div(graficos_otros, style={
            "display": "grid",
            "gap": "30px 40px",
            "gridTemplateColumns": "repeat(auto-fit, minmax(300px, 1fr))",
            "alignItems": "start",
            "width": "100%"
        })
    ])

if __name__ == "__main__":
    app.run(debug=True, port=8051)