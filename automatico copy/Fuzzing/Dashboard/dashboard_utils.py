from dash import dcc, html
import plotly.express as px

def card(fig, tipo='cuadrado', categoria=None):
    style = {
        "backgroundColor": "transparent",
        "padding": "0px",
        "borderRadius": "0px",
        "boxShadow": "none",
        "overflow": "visible",
        "display": "flex",
        "flexDirection": "column",
        "justifyContent": "center"
    }

    if tipo == 'cuadrado':
        style["minHeight"] = "420px"
    elif tipo == 'rectangular':
        style["minHeight"] = "300px"

    # Puedes usar `categoria` para lógica futura si lo deseas
    return html.Div(
        [dcc.Graph(figure=fig, config={"displayModeBar": False})],
        style=style
    )




def crear_grafico_bar(df, x, y, title, color=None, color_discrete_sequence=None, color_continuous_scale=None, category_order=None, show_legend=False):
    fig = px.bar(
        df,
        x=x,
        y=y,
        title=title,
        color=color if color else x,
        color_discrete_sequence=color_discrete_sequence,
        color_continuous_scale=color_continuous_scale
    )

    if category_order:
        fig.update_xaxes(categoryorder='array', categoryarray=category_order)

    fig.update_layout(
        showlegend=show_legend,
        coloraxis_showscale=False,
        xaxis_tickangle=-45,
        height=500,
        margin=dict(t=40, l=20, r=20, b=100),
        title={
            "text": title,
            "y": 0.9,               # ⬅ más bajo que por defecto
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": {"size": 18, "color": "#333"}  # ⬅ tamaño moderado y color claro
        }
    )


    fig.update_xaxes(type="category", dtick=1)
    return fig


    if category_order:
        fig.update_xaxes(categoryorder='array', categoryarray=category_order)

    fig.update_layout(
        showlegend=show_legend,
        coloraxis_showscale=False,
        xaxis_tickangle=-45,           
        height=500                     
    )

    fig.update_xaxes(type="category", dtick=1)  
    return fig

def categorizar_longitud(x):
    if x <= 50: return '0-50'
    elif x <= 100: return '51-100'
    elif x <= 300: return '101-300'
    elif x <= 1000: return '301-1000'
    return '1000+'