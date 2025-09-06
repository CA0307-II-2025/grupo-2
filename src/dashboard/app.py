import pandas as pd
import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import plotly.graph_objects as go

# Cargar y preparar datos (según el notebook)
df = pd.read_excel(r"data\raw\datos_crudos.xlsx").dropna()
df.columns = [
    "ano",
    "evento",
    "categoria",
    "decreto",
    "provincia",
    "canton",
    "latitud",
    "longitud",
    "tipologia",
    "total",
]
df["tipologia"] = (
    df["tipologia"].str.strip().str.upper().str.replace(r"\s+", " ", regex=True)
)

# Análisis de pérdidas por año
perdidas_anuales = df.groupby("ano")["total"].sum().sort_index()
df_perdidas_anuales = perdidas_anuales.reset_index()
df_perdidas_anuales.columns = ["Año", "Pérdidas"]

# Análisis de pérdidas por tipología
perdidas_tipologia = df.groupby("tipologia")["total"].sum().sort_values()
df_perdidas_tipologia = perdidas_tipologia.reset_index()
df_perdidas_tipologia.columns = ["Tipología", "Pérdidas"]

# ==============================
# Dashboard con Dash
# ==============================
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div(
    id="main",
    children=[
        # Encabezado
        html.Div(
            [
                html.H1(
                    "Análisis de pérdidas por desastres naturales en Costa Rica",
                    className="titulo",
                )
            ],
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
                                dcc.Tab(label="Pérdidas por año", value="tab1"),
                                dcc.Tab(label="Pérdidas por tipología", value="tab2"),
                                dcc.Tab(label="Datos detallados", value="tab3"),
                            ],
                        ),
                        html.Hr(),
                        html.Label("Filtrar por año:"),
                        dcc.Dropdown(
                            id="dropdown-anio",
                            options=[
                                {"label": str(int(x)), "value": x}
                                for x in sorted(df["ano"].unique())
                            ],
                            value=sorted(df["ano"].unique())[0],
                            multi=True,
                        ),
                        html.Label("Filtrar por tipología:"),
                        dcc.Dropdown(
                            id="dropdown-tipologia",
                            options=[
                                {"label": x, "value": x}
                                for x in sorted(df["tipologia"].unique())
                            ],
                            value=sorted(df["tipologia"].unique())[0],
                            multi=True,
                        ),
                        html.Label("Rango de años:"),
                        dcc.RangeSlider(
                            id="slider-anio",
                            min=df["ano"].min(),
                            max=df["ano"].max(),
                            step=1,
                            marks={
                                int(ano): str(int(ano)) for ano in df["ano"].unique()
                            },
                            value=[df["ano"].min(), df["ano"].max()],
                        ),
                        html.Br(),
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
            [
                html.H3("Pérdidas anuales por desastres naturales"),
                dcc.Graph(id="grafico-perdidas-anuales"),
                html.Div(
                    [
                        html.H4("Resumen estadístico"),
                        dash_table.DataTable(
                            id="tabla-resumen-anual",
                            columns=[
                                {"name": "Estadística", "id": "Estadística"},
                                {"name": "Valor", "id": "Valor"},
                            ],
                            data=[],
                            page_size=10,
                            style_table={"overflowX": "auto"},
                        ),
                    ]
                ),
            ]
        )
    elif tab == "tab2":
        return html.Div(
            [
                html.H3("Pérdidas por tipología"),
                dcc.Graph(id="grafico-perdidas-tipologia"),
                html.Div(
                    [
                        html.H4("Resumen por tipología"),
                        dash_table.DataTable(
                            id="tabla-resumen-tipologia",
                            columns=[
                                {"name": "Tipología", "id": "Tipología"},
                                {"name": "Pérdidas totales", "id": "Pérdidas totales"},
                                {"name": "Porcentaje", "id": "Porcentaje"},
                            ],
                            data=[],
                            page_size=10,
                            style_table={"overflowX": "auto"},
                        ),
                    ]
                ),
            ]
        )
    else:
        return html.Div(
            [
                html.H3("Datos detallados"),
                dash_table.DataTable(
                    id="tabla-detalles",
                    columns=[{"name": col, "id": col} for col in df.columns],
                    data=df.to_dict("records"),
                    page_size=10,
                    filter_action="native",
                    sort_action="native",
                    export_format="csv",
                    style_table={
                        "overflowX": "auto",
                        "height": "400px",
                        "overflowY": "auto",
                    },
                ),
            ]
        )


@app.callback(
    Output("grafico-perdidas-anuales", "figure"), [Input("slider-anio", "value")]
)
def actualizar_grafico_anual(rango_anio):
    filtered_df = df_perdidas_anuales[
        (df_perdidas_anuales["Año"] >= rango_anio[0])
        & (df_perdidas_anuales["Año"] <= rango_anio[1])
    ]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=filtered_df["Año"],
            y=filtered_df["Pérdidas"],
            mode="lines+markers",
            line=dict(color="royalblue", width=2),
            marker=dict(size=8),
            name="Pérdidas",
        )
    )

    fig.update_layout(
        width=1000,
        height=500,
        template="simple_white",
        title="Pérdidas anuales por desastres naturales en Costa Rica",
        xaxis_title="Año",
        yaxis_title="Pérdidas totales",
        hovermode="x unified",
    )

    return fig


@app.callback(
    Output("grafico-perdidas-tipologia", "figure"),
    [Input("dropdown-tipologia", "value")],
)
def actualizar_grafico_tipologia(tipologias):
    if not tipologias or (isinstance(tipologias, list) and len(tipologias) == 0):
        filtered_df = df_perdidas_tipologia
    else:
        if not isinstance(tipologias, list):
            tipologias = [tipologias]
        filtered_df = df_perdidas_tipologia[
            df_perdidas_tipologia["Tipología"].isin(tipologias)
        ]

    fig = px.bar(
        filtered_df,
        x="Pérdidas",
        y="Tipología",
        orientation="h",
        title="Distribución de Pérdidas por Tipología",
    )

    fig.update_layout(
        xaxis_title="Pérdida en Colones",
        yaxis_title="Tipología",
        xaxis_type="log",  # Escala logarítmica para mejor visualización
    )

    return fig


@app.callback(Output("tabla-resumen-anual", "data"), [Input("slider-anio", "value")])
def actualizar_tabla_anual(rango_anio):
    filtered_df = df_perdidas_anuales[
        (df_perdidas_anuales["Año"] >= rango_anio[0])
        & (df_perdidas_anuales["Año"] <= rango_anio[1])
    ]

    if len(filtered_df) > 0:
        stats = filtered_df["Pérdidas"].describe().reset_index()
        stats.columns = ["Estadística", "Valor"]
        stats["Valor"] = stats["Valor"].apply(lambda x: f"{x:,.2f}")
        return stats.to_dict("records")
    return []


@app.callback(
    Output("tabla-resumen-tipologia", "data"), [Input("dropdown-tipologia", "value")]
)
def actualizar_tabla_tipologia(tipologias):
    if not tipologias or (isinstance(tipologias, list) and len(tipologias) == 0):
        filtered_df = df_perdidas_tipologia
    else:
        if not isinstance(tipologias, list):
            tipologias = [tipologias]
        filtered_df = df_perdidas_tipologia[
            df_perdidas_tipologia["Tipología"].isin(tipologias)
        ]

    total_perdidas = filtered_df["Pérdidas"].sum()
    filtered_df["Porcentaje"] = (filtered_df["Pérdidas"] / total_perdidas * 100).round(
        2
    )
    filtered_df["Pérdidas totales"] = filtered_df["Pérdidas"].apply(
        lambda x: f"₡{x:,.2f}"
    )
    filtered_df["Porcentaje"] = filtered_df["Porcentaje"].apply(lambda x: f"{x}%")

    return filtered_df[["Tipología", "Pérdidas totales", "Porcentaje"]].to_dict(
        "records"
    )


if __name__ == "__main__":
    app.run(debug=True)
