import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import datetime

# ==============================
# 1. Carga y preprocesamiento de datos
# ==============================
df = pd.read_excel("../../data/raw/datos_crudos.xlsx", header=1)

df = df[
    [
        "Serial",
        "Event",
        "&quot;Provincia&quot;",
        "&quot;CantÃ³n&quot;",
        "&quot;Distrito&quot;",
        "&quot;Location&quot;",
        "Date (YMD)",
        "Comments",
        "Cause",
        "Description of Cause",
        "Source",
        "Magnitude",
        "Duration (d)",
        "Other sectors",
        "Deaths",
        "Injured",
        "Missing",
        "Houses Destroyed",
        "Houses Damaged",
        "Directly affected",
        "Indirectly Affected",
        "Relocated",
        "Evacuated",
        "Losses $Local",
        "Education centers",
        "Hospitals",
    ]
]

df.columns = [
    "Serial",
    "Event",
    "Provincia",
    "Canton",
    "Distrito",
    "Ubicacion",
    "Date (YMD)",
    "Comments",
    "Cause",
    "Description of Cause",
    "Source",
    "Magnitude",
    "Duration (d)",
    "Other sectors",
    "Deaths",
    "Injured",
    "Missing",
    "Houses Destroyed",
    "Houses Damaged",
    "Directly affected",
    "Indirectly Affected",
    "Relocated",
    "Evacuated",
    "Losses $Local",
    "Education centers",
    "Hospitals",
]

# Eliminamos nulos en Event y en pérdidas
df = df.dropna(subset=["Event", "Losses $Local"])

# Arreglamos valores que no son numéricos
df = df[df["Losses $Local"] != "AfectaciÃ³n por exceso de escorrentÃ\xada superficial."]
df["Losses $Local"] = df["Losses $Local"].astype(float)

# Conteo de eventos
conteo = pd.DataFrame(df["Event"].value_counts().reset_index())
conteo.columns = ["Event", "count"]

# Frecuencia relativa
conteo["frec_rel"] = conteo["count"] / conteo["count"].sum() * 100

# Promedio de daños por evento
conteo["promedio_danos"] = df.groupby("Event")["Losses $Local"].mean().reset_index(drop=True)

# Normalizamos el promedio de daños
prueba = conteo.copy()
prueba["promedio_danos"] = (
    (prueba["promedio_danos"] - prueba["promedio_danos"].mean())
    / prueba["promedio_danos"].std()
)

# ==============================
# 2. Dashboard con Dash
# ==============================
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div(
    id="main",
    children=[
        # Encabezado
        html.Div(
            [html.H1("Eventos extremos en Costa Rica", className="titulo")],
            className="encabezado",
        ),
        # Portada
        html.Div(
            [
                html.Img(
                    src="assets/ucr_logo.png",
                    style={"height": "80px", "display": "block", "margin": "0 auto"},
                ),
                html.H1(
                    "Dashboard Estadístico - Estadística Actuarial II",
                    style={"textAlign": "center"},
                ),
                html.H3("Proyecto", style={"textAlign": "center", "marginTop": "10px"}),
                html.P(
                    "Autores: Joseph Romero - Dixon Montero - Andrey Prado",
                    style={
                        "textAlign": "center",
                        "fontSize": "18px",
                        "fontStyle": "italic",
                        "marginBottom": "20px",
                    },
                ),
                html.Hr(),
            ]
        ),
        # Cuerpo principal
        html.Div(
            [
                html.Div(
                    [
                        html.H2("Opciones"),
                        dcc.Tabs(
                            id="tabs",
                            value="tab1",
                            children=[
                                dcc.Tab(label="Gráficos", value="tab1"),
                                dcc.Tab(label="Tabla", value="tab2"),
                                dcc.Tab(label="Extras", value="tab3"),
                            ],
                        ),
                        html.Hr(),
                        html.Label("Categoría (decorativo):"),
                        dcc.Dropdown(
                            id="dropdown",
                            options=[{"label": x, "value": x} for x in conteo["Event"].unique()],
                            value=conteo["Event"].iloc[0],
                        ),
                        html.Label("Rango (decorativo):"),
                        dcc.RangeSlider(0, 100, 10, value=[20, 80], id="slider"),
                        html.Br(),
                        dcc.DatePickerRange(
                            id="fechas",
                            start_date=datetime.date(2025, 1, 1),
                            end_date=datetime.date(2025, 12, 31),
                        ),
                    ],
                    className="Menu",
                ),
                html.Div(id="contenido", className="contenido"),
            ],
            className="cuerpo",
        ),
        # Pie de página
        html.Footer("Universidad de Costa Rica - Semestre II", className="pie"),
    ],
)


@app.callback(Output("contenido", "children"), Input("tabs", "value"))
def mostrar_tab(tab):
    if tab == "tab1":
        return html.Div(
            [html.H3("Gráficos"), dcc.Graph(id="grafico1"), dcc.Graph(id="grafico2")]
        )
    elif tab == "tab2":
        return html.Div(
            [
                html.H3("Tabla - Conteo de Eventos"),
                dash_table.DataTable(
                    id="tabla",
                    columns=[{"name": c, "id": c} for c in conteo.columns],
                    data=conteo.to_dict("records"),
                    page_size=10,
                    filter_action="native",
                    sort_action="native",
                    export_format="csv",
                    style_table={"overflowX": "auto"},
                ),
            ]
        )
    else:
        return html.Div(
            [
                html.H3("Extras"),
                html.Button("Descargar", id="btn-descargar"),
                dcc.Download(id="descarga"),
                html.Br(),
                html.H4("Referencias utilizadas"),
                html.Ul(
                    [
                        html.Li(
                            "Plotly Technologies Inc. (n.d.). Dash tutorial. https://dash.plotly.com/tutorial"
                        ),
                        html.Li(
                            "Plotly Technologies Inc. (n.d.). Plotly Python library. https://plotly.com/python/"
                        ),
                    ]
                ),
            ]
        )


@app.callback(
    [Output("grafico1", "figure"), Output("grafico2", "figure")],
    [Input("dropdown", "value"), Input("slider", "value")],
)
def actualizar_graficos(cat, rango):
    # Gráfico 1: Conteo de eventos
    fig1 = px.bar(
        conteo,
        x="count",
        y="Event",
        orientation="h",
        title="Conteo de eventos",
    )

    # Gráfico 2: Promedio de daños estandarizados
    fig2 = px.bar(
        prueba,
        x="promedio_danos",
        y="Event",
        orientation="h",
        title="Promedio de daños (estandarizado)",
    )

    return fig1, fig2


@app.callback(
    Output("descarga", "data"),
    Input("btn-descargar", "n_clicks"),
    prevent_initial_call=True,
)
def descargar_csv(n):
    return dcc.send_data_frame(conteo.to_csv, "conteo_eventos.csv", index=False)


if __name__ == "__main__":
    app.run(debug=True)
