import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import pandas as pd
import datetime
# Referencias consultadas: https://dash.plotly.com/tutorial y https://plotly.com/python/
# Estas fuentes fueron utilizadas para comprender la estructura general de un dashboard interactivo,
# así como para identificar los componentes y comandos necesarios para su implementación en Python.

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
                    "Dashboard Estadístico - Estadistica Actuarial II",
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
                        html.Label("Categoría:"),
                        dcc.Dropdown(
                            id="dropdown",
                            options=[{"label": x, "value": x} for x in ["A", "B", "C"]],
                            value="A",
                        ),
                        html.Label("Rango:"),
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
                html.H3("Tabla"),
                dash_table.DataTable(
                    id="tabla",
                    columns=[{"name": c, "id": c} for c in ["Col1", "Col2", "Col3"]],
                    data=[{"Col1": 1, "Col2": 2, "Col3": 3}],
                    page_size=5,
                    filter_action="native",
                    sort_action="native",
                    export_format="csv",
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
    datos = pd.DataFrame(
        {
            "x": range(10),
            "y": [i**2 for i in range(10)],
            "cat": ["A", "B", "C", "A", "B", "C", "A", "B", "C", "A"],
        }
    )

    filtro = datos[
        (datos["cat"] == cat) & (datos["x"].between(rango[0] // 10, rango[1] // 10))
    ]

    if filtro.empty:
        filtro = pd.DataFrame({"x": [], "y": []})

    fig1 = px.bar(filtro, x="x", y="y", title="Barras")
    fig2 = px.line(filtro, x="x", y="y", title="Líneas")

    return fig1, fig2


@app.callback(
    Output("descarga", "data"),
    Input("btn-descargar", "n_clicks"),
    prevent_initial_call=True,
)
def descargar_csv(n):
    df = pd.DataFrame({"Col1": [1, 2, 3], "Col2": [4, 5, 6]})
    return dcc.send_data_frame(df.to_csv, "datos.csv", index=False)


if __name__ == "__main__":
    app.run(debug=True)
