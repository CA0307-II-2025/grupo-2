import dash
from dash import dcc, html
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
from scipy.stats import lognorm

# Cargar los datos de pérdidas históricas 
# (asegúrese de que 'datos_limpios.csv' esté en el mismo directorio que este script, o ajuste la ruta)
df = pd.read_csv('C:\\Users\\josep\\OneDrive - Universidad de Costa Rica\\UCR\\AÑO 3\\2\\Estadistica\\Proyecto Grupal\\grupo-2\\data\\clean\\datos_limpios.csv')
# Filtrar datos inválidos o faltantes (aseguramos que las pérdidas sean positivas para el análisis)
df = df[df['total'] > 0]

# Cargar el mapa geográfico de provincias de Costa Rica (GeoJSON)
# (asegúrese de que 'provincias.json' esté disponible en el mismo directorio, o ajuste la ruta)
with open('C:\\Users\\josep\\OneDrive - Universidad de Costa Rica\\UCR\\AÑO 3\\2\\Estadistica\\Proyecto Grupal\\grupo-2\\data\\provincias.json', 'r') as f:
    geojson = json.load(f)

# Precalcular información para gráficos estáticos (Inferencia, Modelos, Cópulas):

# 1. Matriz de correlaciones entre pérdidas anuales por provincia (para tab "Cópulas")
prov_year = df.groupby(['ano', 'provincia'])['total'].sum().reset_index()
prov_pivot = prov_year.pivot(index='ano', columns='provincia', values='total').fillna(0)
prov_corr = prov_pivot.corr()

# Crear figura de heatmap de correlación entre provincias
fig_copula = px.imshow(prov_corr, text_auto=".2f", aspect="auto",
                       color_continuous_scale=px.colors.diverging.RdBu, color_continuous_midpoint=0,
                       labels={'x': 'Provincia', 'y': 'Provincia'})
fig_copula.update_layout(title='Correlación de pérdidas entre provincias',
                         margin={'t': 50, 'b': 0}, coloraxis_colorbar_title='Correlación')
fig_copula.update_xaxes(side="bottom")  # Colocar etiquetas de provincias en el eje X abajo

# 2. Distribución de cola de pérdidas (CCDF en escala log-log) para tab "Inferencia"
# Calcular fracción de excedencia: P(X > x)
losses = np.sort(df['total'].values)  # pérdidas ordenadas ascendentemente
n = len(losses)
exceed_prob = [(n - i) / n for i in range(n)]  # P(X > losses[i])
# Crear figura de scatter log-log de la cola de distribución
fig_tail = go.Figure()
fig_tail.add_trace(go.Scatter(x=losses, y=exceed_prob, mode='markers', marker_size=4, name='Datos'))
fig_tail.update_xaxes(type='log', title_text='Pérdida (colones)')
fig_tail.update_yaxes(type='log', title_text='P(X > x)')
fig_tail.update_layout(title="Función de excedencia de pérdidas (escala log-log)")

# 3. Simulación Monte Carlo de pérdidas anuales (usando distribución ajustada a datos históricos)
# Calcular pérdidas totales por año
year_totals = df.groupby('ano')['total'].sum().values
# Ajustar una distribución lognormal a las pérdidas anuales totales
shape, loc, scale = lognorm.fit(year_totals, floc=0)
# Generar simulaciones aleatorias de pérdidas anuales
sims = lognorm.rvs(shape, loc=loc, scale=scale, size=10000, random_state=0)
# Limitar valores extremos para visualización (cortar al percentil 99.9 para evitar cola muy larga)
cutoff = np.quantile(sims, 0.999)
sims_plot = sims[sims <= cutoff]

# Crear figura del histograma de pérdidas anuales simuladas
fig_mc = px.histogram(sims_plot, nbins=50,
                      labels={'value': 'Pérdida anual simulada (colones)', 'count': 'Frecuencia'})
fig_mc.update_layout(title='Distribución simulada de pérdidas anuales', showlegend=False)
fig_mc.update_xaxes(title_text='Pérdida anual (colones)')
fig_mc.update_yaxes(title_text='Frecuencia')
# Añadir línea vertical para percentil 95
p95 = np.percentile(sims, 95)
fig_mc.add_vline(x=p95, line_dash="dash", line_color="red",
                 annotation_text="Percentil 95", annotation_position="top right")

# Calcular estadísticas de simulación para texto explicativo (en miles de millones de colones)
mean_loss = sims.mean()
perc95 = np.percentile(sims, 95)
perc99 = np.percentile(sims, 99)
mean_loss_b = mean_loss / 1e9   # valor en mil millones
perc95_b = perc95 / 1e9         # valor en mil millones
perc99_b = perc99 / 1e9         # valor en mil millones

# Definir la aplicación Dash
app = dash.Dash(__name__)
app.title = "Dashboard Pérdidas CR"

# Listas de opciones únicas para filtros globales
all_provinces = sorted(df['provincia'].unique())
all_categories = sorted(df['categoria'].unique())
all_years = sorted(df['ano'].unique())

# Layout de la aplicación
app.layout = html.Div([
    html.H1("Dashboard de Pérdidas por Desastres Naturales en Costa Rica"),
    html.P("Este tablero interactivo presenta información histórica sobre las pérdidas económicas causadas por desastres naturales en Costa Rica. Puede filtrar los datos por rango de años, por provincia y por categoría de daño para explorar distintos aspectos."),

    # Filtros globales
    html.Div([
        # Filtro de rango de años
        html.Label("Años:", style={'margin-right': '10px'}),
        dcc.RangeSlider(
            id='year-range',
            min=min(all_years), max=max(all_years),
            value=[min(all_years), max(all_years)],
            marks={int(year): str(int(year)) for year in all_years},
            step=None,  # solo permitir selección de años disponibles
            allowCross=False
        ),
        html.Br(),
        # Filtro de provincias (multiselección)
        html.Label("Provincias:", style={'margin-right': '10px'}),
        dcc.Dropdown(
            id='prov-filter',
            options=[{'label': prov, 'value': prov} for prov in all_provinces],
            value=all_provinces,      # por defecto todas las provincias
            multi=True,
            placeholder="Seleccione provincia(s)"
        ),
        # Filtro de categorías (multiselección)
        html.Label("Categorías:", style={'margin': '0px 0px 0px 20px', 'padding-right': '10px'}),
        dcc.Dropdown(
            id='cat-filter',
            options=[{'label': cat, 'value': cat} for cat in all_categories],
            value=all_categories,    # por defecto todas las categorías
            multi=True,
            placeholder="Seleccione categoría(s)"
        )
    ], style={'background-color': '#F9F9F9', 'border': '1px solid #CCC', 'padding': '10px',
              'border-radius': '5px', 'margin-bottom': '20px'}),

    # Pestañas de visualización
    dcc.Tabs([
        dcc.Tab(label="Mapa Interactivo", children=[
            html.H3("Pérdidas Totales por Provincia"),
            html.P("Mapa de Costa Rica que muestra las pérdidas económicas totales acumuladas por provincia en el período seleccionado. El color más oscuro indica mayores pérdidas. Pase el cursor sobre una provincia para ver el monto exacto."),
            # Mapa y gráfica de frecuencia de eventos por provincia, dispuestos en fila
            html.Div([
                dcc.Graph(id='map-graph', style={'flex': '1 1 60%', 'minWidth': '300px', 'height': '450px'}),
                dcc.Graph(id='freq-graph', style={'flex': '1 1 35%', 'minWidth': '300px', 'height': '450px'})
            ], style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'space-around'})
        ]),
        dcc.Tab(label="Pérdidas por Año", children=[
            html.H3("Tendencia de Pérdidas por Año"),
            html.P("Gráfico de barras de las pérdidas totales por año. Permite observar la tendencia temporal y detectar años con desastres particularmente costosos. También se incluye una línea (eje derecho) que muestra el número de eventos ocurridos cada año para visualizar la frecuencia de desastres."),
            dcc.Graph(id='year-graph')
        ]),
        dcc.Tab(label="Pérdidas por Tipología", children=[
            html.H3("Pérdidas por Categoría de Daño"),
            html.P("Pérdidas económicas totales acumuladas según la categoría de daño o tipología (Infraestructura, Social, Hídrico, Productivo u Otros). Este gráfico permite identificar qué tipos de daños han generado las mayores pérdidas en el período seleccionado."),
            dcc.Graph(id='cat-graph')
        ]),
        dcc.Tab(label="Exploratorio", children=[
            html.H3("Análisis Exploratorio de Distribuciones"),
            html.P("Se examina la distribución de las pérdidas por evento individual. A la izquierda se presenta un histograma de las pérdidas (con eje X en escala logarítmica para resaltar la cola de la distribución) y a la derecha un diagrama de caja comparando la distribución de pérdidas por categoría de daño."),
            html.Div([
                dcc.Graph(id='hist-graph', style={'display': 'inline-block', 'width': '50%'}),
                dcc.Graph(id='box-graph', style={'display': 'inline-block', 'width': '50%'})
            ])
        ]),
        dcc.Tab(label="Inferencia", children=[
            html.H3("Resultados Inferenciales"),
            html.P([
                "Mediante pruebas estadísticas se encontró que existen diferencias significativas en las pérdidas según la categoría de daño. Por ejemplo, las pérdidas en la categoría ",
                html.B("Infraestructura"),
                " tienden a ser mayores en promedio que en otras categorías, mientras que ",
                html.B("Social"),
                " presenta montos medios más bajos. También se observaron diferencias en la variabilidad: ciertas categorías muestran una dispersión de pérdidas más amplia (eventos muy extremos ocasionales)."
            ]),
            html.P([
                "El análisis de valores extremos (EVT) reveló que la distribución de pérdidas tiene ",
                html.B("cola pesada"),
                ". Esto significa que, aunque la mayoría de eventos tienen pérdidas moderadas, existe una probabilidad no despreciable de pérdidas extremadamente altas. Un caso ilustrativo es un evento en ",
                html.B("2009 (Alajuela)"),
                " con pérdidas ~2×10^11 colones, muy por encima del resto. Ajustando una distribución Pareto a los datos de cola, se estimó un parámetro de forma (~0.6) mayor que 0, lo que confirma la presencia de colas gruesas en la distribución de pérdidas."
            ]),
            html.P("La siguiente gráfica muestra la fracción de eventos que exceden cierto monto de pérdida, en escala log-log. La porción aproximadamente lineal en el extremo derecho sugiere un comportamiento tipo Pareto en la cola de la distribución de pérdidas (es decir, una disminución lenta de la probabilidad para eventos de gran magnitud)."),
            dcc.Graph(figure=fig_tail, id='tail-graph')
        ]),
        dcc.Tab(label="Modelos (simulación Monte Carlo)", children=[
            html.H3("Simulación Monte Carlo de Pérdidas Anuales"),
            html.P([
                "Utilizando los datos históricos agregados por año, se calibró un modelo probabilístico para las pérdidas anuales totales y se realizaron simulaciones Monte Carlo para estimar escenarios futuros de pérdidas. ",
                html.B("Nota:"),
                " Esta simulación se basa en el conjunto completo de datos históricos (no se filtra por la selección del usuario)."
            ]),
            html.P("El histograma a continuación muestra la distribución simulada de las pérdidas anuales. La línea roja marca el percentil 95, es decir, un nivel de pérdidas que se alcanzaría o superaría aproximadamente 1 vez cada 20 años según el modelo."),
            dcc.Graph(figure=fig_mc, id='mc-graph'),
            html.P([
                "La pérdida anual esperada es aproximadamente ",
                html.B(f"{mean_loss_b:.0f} mil millones"),
                " de colones. El percentil 95 (escenario de 1 en 20 años) es alrededor de ",
                html.B(f"{perc95_b:.0f} mil millones"),
                ", y el percentil 99 (1 en 100 años) cerca de ",
                html.B(f"{perc99_b:.0f} mil millones"),
                " de colones (≈",
                f"{perc99/1e12:.2f}",
                " billones)."
            ])
        ]),
        dcc.Tab(label="Cópulas", children=[
            html.H3("Dependencia entre Provincias (Análisis con Cópulas)"),
            html.P("Se evaluó cómo las pérdidas por desastres se distribuyen simultáneamente entre provincias, para entender si ocurren eventos que afectan a múltiples regiones a la vez. La matriz de correlación presentada a continuación resume la relación entre las pérdidas anuales de cada par de provincias."),
            html.P([
                "Los colores ",
                html.B("rojizos"),
                " indican correlaciones positivas altas (pérdidas elevadas que suelen ocurrir juntas en esas provincias), mientras que los ",
                html.B("azulados"),
                " indican correlaciones negativas o bajas (cuando una provincia sufre pérdidas altas, la otra tiende a no sufrirlas simultáneamente). Se destacan, por ejemplo, pares con alta dependencia: ",
                html.B("San José-Puntarenas"),
                " y ",
                html.B("Heredia-Limón"),
                ", lo que sugiere eventos climáticos que impactan a ambas provincias a la vez."
            ]),
            dcc.Graph(figure=fig_copula, id='copula-graph'),
            html.P([
                "Para modelar este tipo de riesgo multivariante, se utilizaron ",
                html.B("cópulas"),
                " (e.g., cópula t-Student) que permiten simular escenarios de pérdidas conjuntas coherentes con las dependencias observadas, mejorando la estimación de riesgos extremos simultáneos en múltiples regiones."
            ])
        ])
    ]),
    # Créditos / autoría
    html.Div("Desarrollado por Grupo 2 - Universidad de Costa Rica (Autores originales: Jose Andrey Prado Rojas y colaboradores).",
             style={'fontSize': '12px', 'color': 'gray', 'margin-top': '15px', 'textAlign': 'center'})
], style={'fontFamily': 'Arial, sans-serif', 'margin': '20px'})

# Definir colores fijos para categorías (para consistencia en los gráficos)
color_map = {
    'INFRAESTRUCTURA': '#d62728',  # rojo oscuro
    'PRODUCTIVO': '#1f77b4',       # azul
    'SOCIAL': '#2ca02c',           # verde
    'HÍDRICO': '#9467bd',         # púrpura
    'OTROS': '#8c564b'            # café/marrón
}

# Callback para actualizar los gráficos interactivos según los filtros
@app.callback(
    [dash.dependencies.Output('map-graph', 'figure'),
     dash.dependencies.Output('year-graph', 'figure'),
     dash.dependencies.Output('cat-graph', 'figure'),
     dash.dependencies.Output('hist-graph', 'figure'),
     dash.dependencies.Output('box-graph', 'figure'),
     dash.dependencies.Output('freq-graph', 'figure')],
    [dash.dependencies.Input('year-range', 'value'),
     dash.dependencies.Input('prov-filter', 'value'),
     dash.dependencies.Input('cat-filter', 'value')]
)
def update_graphs(year_range, selected_provs, selected_cats):
    # Filtrar datos según la selección del usuario
    start_year, end_year = year_range
    dff = df[(df['ano'] >= start_year) & (df['ano'] <= end_year) &
             (df['provincia'].isin(selected_provs)) &
             (df['categoria'].isin(selected_cats))]
    # Si no hay datos después del filtrado, devolver figuras vacías con mensaje
    if dff.empty:
        fig_empty = go.Figure()
        fig_empty.update_xaxes(showgrid=False, visible=False)
        fig_empty.update_yaxes(showgrid=False, visible=False)
        fig_empty.add_annotation(text="No hay datos para la selección realizada",
                                 xref="paper", yref="paper", showarrow=False, font_size=14,
                                 x=0.5, y=0.5)
        return fig_empty, fig_empty, fig_empty, fig_empty, fig_empty, fig_empty

    # 1. Mapa coroplético por provincia (total de pérdidas por provincia)
    prov_data = dff.groupby('provincia', as_index=False)['total'].sum()
    fig_map = px.choropleth(
        prov_data, geojson=geojson, locations='provincia', featureidkey='properties.name',
        color='total', color_continuous_scale='OrRd',
        labels={'provincia': 'Provincia', 'total': 'Pérdidas (colones)'}
    )
    fig_map.update_geos(fitbounds="locations", visible=False)
    fig_map.update_coloraxes(colorbar_title="Colones", colorbar_tickformat=",.0f")
    fig_map.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    # 2. Pérdidas por año (barras) con número de eventos (línea)
    yearly = dff.groupby('ano', as_index=False)['total'].sum().sort_values('ano')
    # Calcular número de eventos únicos por año (considerando eventos identificados por combinación de año+ubicación)
    unique_events = dff.drop_duplicates(subset=['ano', 'provincia', 'canton', 'latitud', 'longitud'])
    events_by_year = unique_events.groupby('ano').size().reindex(yearly['ano'], fill_value=0)
    fig_year = go.Figure()
    fig_year.add_trace(go.Bar(x=yearly['ano'], y=yearly['total'], name='Pérdidas (colones)', marker_color='#C0392B'))
    fig_year.add_trace(go.Scatter(x=events_by_year.index, y=events_by_year.values, mode='lines+markers',
                                  name='Número de eventos', marker_color='#2ca02c', yaxis='y2'))
    fig_year.update_layout(
        xaxis=dict(dtick=1, title='Año'),
        yaxis=dict(title='Pérdidas (colones)', tickformat=",.0f"),
        yaxis2=dict(title='Número de eventos', overlaying='y', side='right'),
        legend=dict(y=1.15, x=0.01)
    )

    # 3. Pérdidas por categoría (barras)
    cat_sum = dff.groupby('categoria', as_index=False)['total'].sum().sort_values('total', ascending=False)
    fig_cat = px.bar(cat_sum, x='categoria', y='total',
                     labels={'categoria': 'Categoría', 'total': 'Pérdidas (colones)'},
                     color='categoria', color_discrete_map=color_map)
    fig_cat.update_layout(showlegend=False)
    fig_cat.update_yaxes(title_text='Pérdidas (colones)', tickformat=",.0f")

    # 4. Histograma de distribución de pérdidas por evento
    filtered_totals = dff['total']
    filtered_totals = filtered_totals[filtered_totals > 0]


    if filtered_totals.empty:
        fig_hist = go.Figure()
        fig_hist.update_layout(
            title="No hay datos válidos para el histograma",
            xaxis_title='Pérdida por evento (colones) [escala log]',
            yaxis_title='Frecuencia'
        )
    else:
        fig_hist = px.histogram(filtered_totals, nbins=50, log_x=True,
                                labels={'value': 'Pérdida por evento (colones)'})
        fig_hist.update_layout(
            xaxis_title='Pérdida por evento (colones) [escala log]',
            yaxis_title='Frecuencia'
        )

    # 5. Diagrama de caja de pérdidas por categoría
    fig_box = px.box(dff, x='total', y='categoria', color='categoria',
                     color_discrete_map=color_map, orientation='h', log_x=True,
                     labels={'categoria': 'Categoría', 'total': 'Pérdida (colones)'})
    fig_box.update_layout(xaxis_title='Pérdida por evento (colones) [escala log]',
                          yaxis_title='Categoría', showlegend=False)

    # 6. Frecuencia de eventos por provincia (barras horizontales)
    # Contar eventos únicos por provincia (misma lógica: agrupar por provincia en datos filtrados únicos)
    events_by_prov = unique_events['provincia'].value_counts().reset_index()
    events_by_prov.columns = ['provincia', 'count']
    events_by_prov = events_by_prov.sort_values('count', ascending=False)
    fig_freq = px.bar(events_by_prov, x='count', y='provincia', orientation='h',
                      labels={'count': 'Número de eventos', 'provincia': 'Provincia'})
    fig_freq.update_layout(margin={'l': 100, 'r': 30, 'b': 30, 't': 30})

    return fig_map, fig_year, fig_cat, fig_hist, fig_box, fig_freq

# Ejecutar la aplicación (modo local)
if __name__ == '__main__':
    app.run(debug=False)
