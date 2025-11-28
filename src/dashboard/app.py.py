import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
from scipy.stats import lognorm
import os
PRIMARY = "#005DA4"   
SECONDARY = "#00A37A" 
ACCENT = "#F39C12"    
BACKGROUND = "#f7f7f7"

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(CURRENT_DIR)
df = pd.read_csv(r"../../data/clean/datos_limpios.csv")
FIG_DIR = os.path.join(CURRENT_DIR, "assets", "figuras")
fig_files = []
if os.path.exists(FIG_DIR):
    for fname in os.listdir(FIG_DIR):
        if fname.lower().endswith((".png", ".jpg", ".jpeg")):
            fig_files.append(fname)

fig_meta = []
for fname in fig_files:
    name, ext = os.path.splitext(fname)
    parts = name.split("_")
    tipo = parts[0]  
    detalle = "_".join(parts[1:]) if len(parts) > 1 else ""
    fig_meta.append({"file": fname, "tipo": tipo, "detalle": detalle})
fig_df = pd.DataFrame(fig_meta)
if not fig_df.empty:
    all_tipos_fig = sorted(fig_df["tipo"].unique())
else:
    all_tipos_fig = []
df = df[df["total"] > 0]
with open(
    r"../../data/provincias.json",
    "r",
) as f:
    geojson = json.load(f)
prov_year = df.groupby(["ano", "provincia"])["total"].sum().reset_index()
prov_pivot = prov_year.pivot(index="ano", columns="provincia", values="total").fillna(0)
prov_corr = prov_pivot.corr()
fig_copula = px.imshow(
    prov_corr,
    text_auto=".2f",
    aspect="auto",
    color_continuous_scale=px.colors.diverging.RdBu,
    color_continuous_midpoint=0,
    labels={"x": "Provincia", "y": "Provincia"},
)
fig_copula.update_layout(
    title="Correlación de pérdidas entre provincias",
    margin={"t": 50, "b": 0},
    coloraxis_colorbar_title="Correlación",
)
fig_copula.update_xaxes(
    side="bottom"
)  
losses = np.sort(df["total"].values)  
n = len(losses)
exceed_prob = [(n - i) / n for i in range(n)]  # P(X > losses[i])
fig_tail = go.Figure()
fig_tail.add_trace(
    go.Scatter(x=losses, y=exceed_prob, mode="markers", marker_size=4, name="Datos")
)
fig_tail.update_xaxes(type="log", title_text="Pérdida (colones)")
fig_tail.update_yaxes(type="log", title_text="P(X > x)")
fig_tail.update_layout(title="Función de excedencia de pérdidas (escala log-log)")
year_totals = df.groupby("ano")["total"].sum().values
shape, loc, scale = lognorm.fit(year_totals, floc=0)
sims = lognorm.rvs(shape, loc=loc, scale=scale, size=10000, random_state=0)
cutoff = np.quantile(sims, 0.999)
sims_plot = sims[sims <= cutoff]
fig_mc = px.histogram(
    sims_plot,
    nbins=50,
    labels={"value": "Pérdida anual simulada (colones)", "count": "Frecuencia"},
)
fig_mc.update_layout(
    title="Distribución simulada de pérdidas anuales", showlegend=False
)
fig_mc.update_xaxes(title_text="Pérdida anual (colones)")
fig_mc.update_yaxes(title_text="Frecuencia")
p95 = np.percentile(sims, 95)
fig_mc.add_vline(
    x=p95,
    line_dash="dash",
    line_color="red",
    annotation_text="Percentil 95",
    annotation_position="top right",
)
mean_loss = sims.mean()
perc95 = np.percentile(sims, 95)
perc99 = np.percentile(sims, 99)
mean_loss_b = mean_loss / 1e9  # valor en mil millones
perc95_b = perc95 / 1e9  # valor en mil millones
perc99_b = perc99 / 1e9  # valor en mil millones
external_stylesheets = [dbc.themes.FLATLY]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Dashboard Pérdidas CR"
all_provinces = sorted(df["provincia"].unique())
all_categories = sorted(df["categoria"].unique())
all_years = sorted(df["ano"].unique())
all_sectors = sorted(df["sector"].unique())

navbar = dbc.Navbar(
    dbc.Container(
        [
            # Logo UCR
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.Img(src=app.get_asset_url("ucr_logo.png"), height="45px")),
                        dbc.Col(
                            html.Div(
                                [
                                    html.Div("Universidad de Costa Rica", style={"fontWeight": "bold", "fontSize": "18px"}),
                                    html.Div("Proyecto Estadística · Grupo 2", style={"fontSize": "13px"}),
                                ]
                            ),
                            className="ms-2",
                        ),
                    ],
                    align="center",
                    className="g-0",
                ),
                href="#",
                style={"textDecoration": "none", "color": "white"},
            ),
        ],
        fluid=True,
    ),
    color="dark",
    dark=True,
    sticky="top",
)
app.layout = html.Div(
    [
        navbar, 

        dbc.Container(
            [
                html.H1(
                    "Dependencia espacial y severidad extrema de pérdidas económicas por desastres naturales en Costa Rica",
                    className="mt-4 mb-2"
                ),

                html.P(
                    "Este tablero interactivo presenta información histórica sobre las pérdidas económicas causadas por desastres naturales en Costa Rica.",
                    className="text-muted"
                ),

                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4("Filtros", className="card-title"),

                            html.Br(),
                            html.Label("Años:", className="fw-bold"),
                            dcc.RangeSlider(
                                id="year-range",
                                min=min(all_years),
                                max=max(all_years),
                                value=[min(all_years), max(all_years)],
                                marks={int(y): str(int(y)) for y in all_years},
                                step=None,
                            ),

                            html.Br(),

                            html.Div(
                                [
                                    # provincias
                                    html.Div(
                                        [
                                            html.Label("Provincias:", className="fw-bold"),
                                            dcc.Dropdown(
                                                id="prov-filter",
                                                options=[{"label": p, "value": p} for p in all_provinces],
                                                value=all_provinces,
                                                multi=True,
                                            ),
                                        ],
                                        className="col-md-4",
                                    ),
                                    # categorias
                                    html.Div(
                                        [
                                            html.Label("Categorías:", className="fw-bold"),
                                            dcc.Dropdown(
                                                id="cat-filter",
                                                options=[{"label": c, "value": c} for c in all_categories],
                                                value=all_categories,
                                                multi=True,
                                            ),
                                        ],
                                        className="col-md-4",
                                    ),
                                    # sector
                                    html.Div(
                                        [
                                            html.Label("Tipo de daño (sector):", className="fw-bold"),
                                            dcc.Dropdown(
                                                id="sector-filter",
                                                options=[{"label": s, "value": s} for s in all_sectors],
                                                value=all_sectors,
                                                multi=True,
                                            ),
                                        ],
                                        className="col-md-4",
                                    ),
                                ],
                                className="row g-3",
                            ),
                        ]
                    ),
                    className="shadow-sm mb-4",
                ),
                dbc.Card(
                    dbc.CardBody(
                        dcc.Tabs(
                            [
                dcc.Tab(
                    label="Mapa Interactivo",
                    children=[
                        html.H3("Pérdidas Totales por Provincia"),
                        html.P(
                            "Mapa de Costa Rica que muestra las pérdidas económicas totales acumuladas por provincia en el período seleccionado. El color más oscuro indica mayores pérdidas. Pase el cursor sobre una provincia para ver el monto exacto."
                        ),
                        html.Div(
                            [
                                dcc.Graph(
                                    id="map-graph",
                                    style={
                                        "flex": "1 1 60%",
                                        "minWidth": "300px",
                                        "height": "450px",
                                    },
                                ),
                                dcc.Graph(
                                    id="freq-graph",
                                    style={
                                        "flex": "1 1 35%",
                                        "minWidth": "300px",
                                        "height": "450px",
                                    },
                                ),
                            ],
                            style={
                                "display": "flex",
                                "flexWrap": "wrap",
                                "justifyContent": "space-around",
                            },
                        ),
                    ],
                ),
                dcc.Tab(
                    label="Pérdidas por Año",
                    children=[
                        html.H3("Tendencia de Pérdidas por Año"),
                        html.P(
                            "Gráfico de barras de las pérdidas totales por año. Permite observar la tendencia temporal y detectar años con desastres particularmente costosos. También se incluye una línea (eje derecho) que muestra el número de eventos ocurridos cada año para visualizar la frecuencia de desastres."
                        ),
                        dcc.Graph(id="year-graph"),
                    ],
                ),
                dcc.Tab(
                    label="Pérdidas por Tipología",
                    children=[
                        html.H3("Pérdidas por Categoría de Daño"),
                        html.P(
                            "Pérdidas económicas totales acumuladas según la categoría de daño o tipología (Infraestructura, Social, Hídrico, Productivo u Otros). Este gráfico permite identificar qué tipos de daños han generado las mayores pérdidas en el período seleccionado."
                        ),
                        dcc.Graph(id="cat-graph"),
                    ],
                ),
            
                dcc.Tab(
                    label="Inferencia",
                    children=[
                        html.H3("Resultados Inferenciales"),
                        html.P(
                            [
                                "Mediante pruebas estadísticas se encontró que existen diferencias significativas en las pérdidas según la categoría de daño. Por ejemplo, las pérdidas en la categoría ",
                                html.B("Infraestructura"),
                                " tienden a ser mayores en promedio que en otras categorías, mientras que ",
                                html.B("Social"),
                                " presenta montos medios más bajos. También se observaron diferencias en la variabilidad: ciertas categorías muestran una dispersión de pérdidas más amplia (eventos muy extremos ocasionales).",
                            ]
                        ),
                        html.P(
                            [
                                "El análisis de valores extremos (EVT) reveló que la distribución de pérdidas tiene ",
                                html.B("cola pesada"),
                                ". Esto significa que, aunque la mayoría de eventos tienen pérdidas moderadas, existe una probabilidad no despreciable de pérdidas extremadamente altas. Un caso ilustrativo es un evento en ",
                                html.B("2009 (Alajuela)"),
                                " con pérdidas ~2×10^11 colones, muy por encima del resto. Ajustando una distribución Pareto a los datos de cola, se estimó un parámetro de forma (~0.6) mayor que 0, lo que confirma la presencia de colas gruesas en la distribución de pérdidas.",
                            ]
                        ),
                        html.P(
                            "La siguiente gráfica muestra la fracción de eventos que exceden cierto monto de pérdida, en escala log-log. La porción aproximadamente lineal en el extremo derecho sugiere un comportamiento tipo Pareto en la cola de la distribución de pérdidas (es decir, una disminución lenta de la probabilidad para eventos de gran magnitud)."
                        ),
                        dcc.Graph(figure=fig_tail, id="tail-graph"),
                    ],
                ),
                dcc.Tab(
                    label="Modelos (simulación Monte Carlo)",
                    children=[
                        html.H3("Simulación Monte Carlo de Pérdidas Anuales"),
                        html.P(
                            [
                                "Utilizando los datos históricos agregados por año, se calibró un modelo probabilístico para las pérdidas anuales totales y se realizaron simulaciones Monte Carlo para estimar escenarios futuros de pérdidas. ",
                                html.B("Nota:"),
                                " Esta simulación se basa en el conjunto completo de datos históricos (no se filtra por la selección del usuario).",
                            ]
                        ),
                        html.P(
                            "El histograma a continuación muestra la distribución simulada de las pérdidas anuales. La línea roja marca el percentil 95, es decir, un nivel de pérdidas que se alcanzaría o superaría aproximadamente 1 vez cada 20 años según el modelo."
                        ),
                        dcc.Graph(figure=fig_mc, id="mc-graph"),
                        html.P(
                            [
                                "La pérdida anual esperada es aproximadamente ",
                                html.B(f"{mean_loss_b:.0f} mil millones"),
                                " de colones. El percentil 95 (escenario de 1 en 20 años) es alrededor de ",
                                html.B(f"{perc95_b:.0f} mil millones"),
                                ", y el percentil 99 (1 en 100 años) cerca de ",
                                html.B(f"{perc99_b:.0f} mil millones"),
                                " de colones (≈",
                                f"{perc99 / 1e12:.2f}",
                                " billones).",
                            ]
                        ),
                    ],
                ),
                dcc.Tab(
                    label="Cópulas",
                    children=[
                        html.H3("Dependencia entre Provincias (Análisis con Cópulas)"),
                        html.P(
                            "Se evaluó cómo las pérdidas por desastres se distribuyen simultáneamente entre provincias, para entender si ocurren eventos que afectan a múltiples regiones a la vez. La matriz de correlación presentada a continuación resume la relación entre las pérdidas anuales de cada par de provincias."
                        ),
                        html.P(
                            [
                                "Los colores ",
                                html.B("rojizos"),
                                " indican correlaciones positivas altas (pérdidas elevadas que suelen ocurrir juntas en esas provincias), mientras que los ",
                                html.B("azulados"),
                                " indican correlaciones negativas o bajas (cuando una provincia sufre pérdidas altas, la otra tiende a no sufrirlas simultáneamente). Se destacan, por ejemplo, pares con alta dependencia: ",
                                html.B("San José-Puntarenas"),
                                " y ",
                                html.B("Heredia-Limón"),
                                ", lo que sugiere eventos climáticos que impactan a ambas provincias a la vez.",
                            ]
                        ),
                        dcc.Graph(figure=fig_copula, id="copula-graph"),
                        html.P(
                            [
                                "Para modelar este tipo de riesgo multivariante, se utilizaron ",
                                html.B("cópulas"),
                                " (e.g., cópula t-Student) que permiten simular escenarios de pérdidas conjuntas coherentes con las dependencias observadas, mejorando la estimación de riesgos extremos simultáneos en múltiples regiones.",
                            ]
                        ),
                    ],
                ),
                dcc.Tab(
                    label="Figuras EVT / Colas",
                    children=[
                        html.H3("Figuras pre-generadas (colas, umbrales, histogramas)"),
                        html.P(
                            "Seleccione el tipo de figura y el detalle (provincia, categoría o total) para visualizar las gráficas generadas en el análisis de colas y umbrales."
                        ),
                        html.Div(
                            [
                                html.Label("Tipo de figura:"),
                                dcc.Dropdown(
                                    id="fig-tipo",
                                    options=[
                                        {"label": t.capitalize(), "value": t}
                                        for t in all_tipos_fig
                                    ],
                                    value=all_tipos_fig[0] if all_tipos_fig else None,
                                    clearable=False,
                                    placeholder="Seleccione tipo de figura",
                                ),
                                html.Br(),
                                html.Label("Detalle (provincia / total / categoría):"),
                                dcc.Dropdown(
                                    id="fig-detalle",
                                    options=[],  
                                    value=None,
                                    placeholder="Seleccione qué quiere ver ",
                                ),
                            ],
                            style={
                                "background-color": "#F9F9F9",
                                "border": "1px solid #CCC",
                                "padding": "10px",
                                "border-radius": "5px",
                                "margin-bottom": "20px",
                                "maxWidth": "600px",
                            },
                        ),
                        html.Div(
                            id="fig-container",
                            style={"textAlign": "center", "marginTop": "20px"},
                        ),
                    ],
                ),
            ]
                        )
                    ),
                    className="shadow-sm"
                ),

                html.Hr(),
                html.Div(
                    [
                        html.Div("Desarrollado por Grupo 2 – Estadística UCR", className="fw-bold"),
                        html.Div(
                            "Autores: Jose Andrey Prado Rojas, Joseph Romero , Dixon Montero , Holmar Rivera.",
                            className="text-muted",
                            style={"fontSize": "13px"},
                        ),
                        html.Div(
                            "II Semestre 2025 · Escuela de Matemática",
                            className="text-muted",
                            style={"fontSize": "12px"},
                        ),
                    ],
                    className="text-center mt-4 mb-4",
                ),
            ],
            fluid=True,
        ),
    ]
)




color_map = {
    "INFRAESTRUCTURA": PRIMARY,
    "PRODUCTIVO": SECONDARY,
    "SOCIAL": "#2980B9",  
    "HÍDRICO": "#16A085", 
    "OTROS": "#7F8C8D",    
}



@app.callback(
    [
        dash.dependencies.Output("map-graph", "figure"),
        dash.dependencies.Output("year-graph", "figure"),
        dash.dependencies.Output("cat-graph", "figure"),
        dash.dependencies.Output("freq-graph", "figure"),
    ],
    [
        dash.dependencies.Input("year-range", "value"),
        dash.dependencies.Input("prov-filter", "value"),
        dash.dependencies.Input("cat-filter", "value"),
        dash.dependencies.Input("sector-filter", "value"), 
    ],
)
def update_graphs(year_range, selected_provs, selected_cats, selected_sectors): 

    start_year, end_year = year_range
    dff = df[
        (df["ano"] >= start_year)
        & (df["ano"] <= end_year)
        & (df["provincia"].isin(selected_provs))
        & (df["categoria"].isin(selected_cats))
        & (df["sector"].isin(selected_sectors))   
    ]

    if dff.empty:
        fig_empty = go.Figure()
        fig_empty.update_xaxes(showgrid=False, visible=False)
        fig_empty.update_yaxes(showgrid=False, visible=False)
        fig_empty.add_annotation(
            text="No hay datos para la selección realizada",
            xref="paper",
            yref="paper",
            showarrow=False,
            font_size=14,
            x=0.5,
            y=0.5,
        )
        return fig_empty, fig_empty, fig_empty, fig_empty

    prov_data = dff.groupby("provincia", as_index=False)["total"].sum()
    fig_map = px.choropleth(
        prov_data,
        geojson=geojson,
        locations="provincia",
        featureidkey="properties.name",
        color="total",
        color_continuous_scale="Blues",
        labels={"provincia": "Provincia", "total": "Pérdidas (colones)"},
    )
    fig_map.update_geos(fitbounds="locations", visible=False)
    fig_map.update_coloraxes(colorbar_title="Colones", colorbar_tickformat=",.0f")
    fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    yearly = dff.groupby("ano", as_index=False)["total"].sum().sort_values("ano")
    unique_events = dff.drop_duplicates(
        subset=["ano", "provincia", "canton", "latitud", "longitud"]
    )
    events_by_year = (
        unique_events.groupby("ano").size().reindex(yearly["ano"], fill_value=0)
    )
    fig_year = go.Figure()
    fig_year.add_trace(
        go.Bar(
            x=yearly["ano"],
            y=yearly["total"],
            name="Pérdidas (colones)",
            marker_color=PRIMARY,
        )
    )
    fig_year.add_trace(
        go.Scatter(
            x=events_by_year.index,
            y=events_by_year.values,
            mode="lines+markers",
            name="Número de eventos",
            marker_color=SECONDARY,
            yaxis="y2",
        )
    )

    fig_year.update_layout(
        xaxis=dict(dtick=1, title="Año"),
        yaxis=dict(title="Pérdidas (colones)", tickformat=",.0f"),
        yaxis2=dict(title="Número de eventos", overlaying="y", side="right"),
        legend=dict(y=1.15, x=0.01),
    )
    cat_sum = (
        dff.groupby("sector", as_index=False)["total"]
        .sum()
        .sort_values("total", ascending=False)
    )
    fig_cat = px.bar(
        cat_sum,
        x="sector",
        y="total",
        labels={"sector": "Tipo de daño (sector)", "total": "Pérdidas (colones)"},
        color="sector",
        color_discrete_map=color_map,
    )
    fig_cat.update_layout(showlegend=False)
    fig_cat.update_yaxes(title_text="Pérdidas (colones)", tickformat=",.0f")
    events_by_prov = unique_events["provincia"].value_counts().reset_index()
    events_by_prov.columns = ["provincia", "count"]
    events_by_prov = events_by_prov.sort_values("count", ascending=False)
    fig_freq = px.bar(
        events_by_prov,
        x="count",
        y="provincia",
        orientation="h",
        labels={"count": "Número de eventos", "provincia": "Provincia"},
    )
    fig_freq.update_layout(margin={"l": 100, "r": 30, "b": 30, "t": 30})
    return fig_map, fig_year, fig_cat, fig_freq
from dash.dependencies import Input, Output, State
@app.callback(
    [Output("fig-detalle", "options"),
     Output("fig-detalle", "value")],
    Input("fig-tipo", "value"),
)
def actualizar_detalle_figuras(tipo_seleccionado):
    if not tipo_seleccionado or fig_df.empty:
        return [], None
    sub = fig_df[fig_df["tipo"] == tipo_seleccionado]
    opciones = []
    for _, row in sub.iterrows():
        if row["detalle"]:
            etiqueta = row["detalle"].replace("_", " ").title()
        else:
            etiqueta = row["file"]
        opciones.append({"label": etiqueta, "value": row["file"]})
    valor_defecto = opciones[0]["value"] if opciones else None
    return opciones, valor_defecto

@app.callback(
    Output("fig-container", "children"),
    [Input("fig-detalle", "value"),
     Input("fig-tipo", "value")],
)
def mostrar_figura_archivo(archivo_seleccionado, tipo_seleccionado):
    if not archivo_seleccionado:
        return html.P(
            "Seleccione un tipo de figura y un detalle para visualizar la imagen.",
            style={"fontStyle": "italic"},
        )
    img_src = app.get_asset_url(f"figuras/{archivo_seleccionado}")
    titulo = f"Figura: {tipo_seleccionado} – {archivo_seleccionado}"

    return html.Div(
        [
            html.Img(
                src=img_src,
                style={
                    "maxWidth": "100%",
                    "height": "auto",
                    "border": "1px solid #CCC",
                    "borderRadius": "5px",
                },
            ),
            html.P(
                titulo,
                style={"marginTop": "10px", "fontStyle": "italic", "color": "gray"},
            ),
        ]
    )
if __name__ == "__main__":
    app.run(debug=False)
