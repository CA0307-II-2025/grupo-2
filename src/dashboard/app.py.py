import os
import sys
import base64
import hashlib
import pandas as pd
import dash
from dash import dcc, html, Input, Output, dash_table, callback
import plotly.express as px
import plotly.graph_objects as go

# =========================
# RUTAS WINDOWS CONFIRMADAS
# =========================
GRUPO2_ROOT = r"C:\Users\josep\OneDrive - Universidad de Costa Rica\UCR\AÑO 3\2\Estadistica\Proyecto Grupal\grupo-2"
RAW_DATA_DIR = os.path.join(GRUPO2_ROOT, "data", "raw")
DASH_DIR = os.path.join(GRUPO2_ROOT, "src", "dashboard")
ASSETS_DIR = os.path.join(DASH_DIR, "assets")
SCRIPTS_DIR = os.path.join(GRUPO2_ROOT, "src", "scripts")

SRC_DIR = os.path.join(GRUPO2_ROOT, "src")
if os.path.isdir(SRC_DIR) and SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# =========================
# CARGA DE DATOS
# =========================
CANDIDATES = [
    os.path.join(RAW_DATA_DIR, "datos_crudos.xlsx"),
    os.path.join(RAW_DATA_DIR, "DATOS_CRUDOS.xlsx"),
    os.path.join("datos_crudos.xlsx"),  # fallback local
]


def load_df():
    last_err = None
    for p in CANDIDATES:
        if os.path.exists(p):
            try:
                df = pd.read_excel(p).dropna(how="all")
                # Asegura 10 columnas con el orden esperado
                if len(df.columns) >= 10:
                    df = df.iloc[:, :10].copy()
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
                    df["tipologia"]
                    .astype(str)
                    .str.strip()
                    .str.upper()
                    .str.replace(r"\s+", " ", regex=True)
                )
                for c in ["ano", "total", "latitud", "longitud"]:
                    if c in df.columns:
                        df[c] = pd.to_numeric(df[c], errors="coerce")
                return df, p
            except Exception as e:
                last_err = f"Error leyendo {p}: {e}"
    return pd.DataFrame(
        columns=[
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
    ), (last_err or f"No encontré 'datos_crudos.xlsx' en {RAW_DATA_DIR}")


df, data_info = load_df()

# Derivados base (no se crean nuevos gráficos; solo estos dos agregados y la tabla de datos)
if not df.empty:
    df_perdidas_anuales = (
        df.groupby("ano")["total"]
        .sum()
        .sort_index()
        .reset_index()
        .rename(columns={"ano": "Año", "total": "Pérdidas"})
    )
    df_perdidas_tipologia = (
        df.groupby("tipologia")["total"]
        .sum()
        .sort_values()
        .reset_index()
        .rename(columns={"tipologia": "Tipología", "total": "Pérdidas"})
    )
else:
    df_perdidas_anuales = pd.DataFrame(columns=["Año", "Pérdidas"])
    df_perdidas_tipologia = pd.DataFrame(columns=["Tipología", "Pérdidas"])


# =========================
# LOGO UCR
# =========================
def logo_component():
    candidates = [
        os.path.join(ASSETS_DIR, "ucr_logo.png"),
        os.path.join(ASSETS_DIR, "LogoUCR.png"),
        os.path.join("assets", "ucr_logo.png"),
        os.path.join("assets", "LogoUCR.png"),
        "ucr_logo.png",
        "LogoUCR.png",
    ]
    for p in candidates:
        if os.path.exists(p):
            # Si está dentro de assets, usar ruta relativa (servida por Dash)
            if "assets" in os.path.normpath(p).split(os.sep):
                return html.Img(
                    src="assets/" + os.path.basename(p),
                    style={"height": "80px", "display": "block", "margin": "0 auto"},
                )
            with open(p, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("ascii")
            ext = os.path.splitext(p)[1].lstrip(".").lower()
            return html.Img(
                src=f"data:image/{ext};base64,{b64}",
                style={"height": "80px", "display": "block", "margin": "0 auto"},
            )
    return html.Div(
        "Logo UCR no encontrado",
        style={"textAlign": "center", "color": "#888", "fontStyle": "italic"},
    )


# =========================
# UTILIDADES PARA GRÁFICOS EXISTENTES
# =========================
IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif"}


def _b64_img(path: str) -> str:
    with open(path, "rb") as f:
        data = f.read()
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    return f"data:image/{ext};base64," + base64.b64encode(data).decode("ascii")


def _hash_file(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def find_images_by_keywords(keywords):
    """Busca imágenes ya generadas por tus scripts/notebooks y las filtra por palabras clave."""
    roots = [
        SCRIPTS_DIR,
        os.path.join(SCRIPTS_DIR, "outputs"),
        os.path.join(SCRIPTS_DIR, "figs"),
        os.path.join(SCRIPTS_DIR, "images"),
        DASH_DIR,
        os.getcwd(),
    ]
    seen, out = set(), []
    for root in roots:
        if not (root and os.path.isdir(root)):
            continue
        for name in os.listdir(root):
            path = os.path.join(root, name)
            ext = os.path.splitext(name)[1].lower()
            lower = name.lower()
            if os.path.isfile(path) and ext in IMG_EXTS:
                # Evitar íconos/logos/tiny files irrelevantes
                if os.path.getsize(path) < 15000 or any(
                    k in lower for k in ["logo", "icon", "ucr", "thumb", "placeholder"]
                ):
                    continue
                if keywords and not any(kw in lower for kw in keywords):
                    continue
                h = _hash_file(path)
                if h in seen:
                    continue
                seen.add(h)
                out.append(path)
    return sorted(out)


def collect_plotly_figs(prefixes=None):
    """
    Importa src\scripts\plots.py y llama funciones sin argumentos que retornen Plotly Figure.
    NO crea gráficos nuevos: solo usa lo que ya exista como funciones exportadas.
    """
    figs = []
    try:
        import importlib
        import inspect

        if SCRIPTS_DIR not in sys.path:
            sys.path.insert(0, SCRIPTS_DIR)
        mod = importlib.import_module("plots")
        for name in dir(mod):
            if name.startswith("_"):
                continue
            obj = getattr(mod, name)
            if callable(obj):
                try:
                    sig = inspect.signature(obj)
                    if len(sig.parameters) == 0:
                        res = obj()
                        if hasattr(res, "to_dict") and hasattr(res, "data"):
                            if (prefixes is None) or any(
                                name.lower().startswith(p) for p in prefixes
                            ):
                                figs.append((name, res))
                except Exception:
                    pass
    except Exception:
        pass
    return figs


def gallery(paths):
    """Muestra una grilla limpia con las imágenes dadas."""
    if not paths:
        return html.Div(
            "No hay imágenes detectadas todavía.",
            style={"color": "#666", "fontStyle": "italic"},
        )
    cards = []
    for p in paths:
        cards.append(
            html.Figure(
                [
                    html.Img(
                        src=_b64_img(p), style={"width": "100%", "height": "auto"}
                    ),
                    html.Figcaption(
                        os.path.basename(p),
                        style={
                            "textAlign": "center",
                            "fontStyle": "italic",
                            "fontSize": "0.9rem",
                        },
                    ),
                ],
                style={
                    "background": "#fff",
                    "border": "1px solid #eee",
                    "borderRadius": "12px",
                    "padding": "8px",
                    "boxShadow": "0 2px 8px rgba(0,0,0,0.05)",
                    "marginBottom": "12px",
                },
            )
        )
    return html.Div(
        cards,
        style={
            "display": "grid",
            "gridTemplateColumns": "repeat(auto-fill, minmax(320px, 1fr))",
            "gap": "14px",
            "alignItems": "start",
        },
    )


# =========================
# APP
# =========================
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div(
    id="main",
    children=[
        html.Div(
            [
                html.H1(
                    "Análisis de pérdidas por desastres naturales en Costa Rica",
                    className="titulo",
                )
            ],
            className="encabezado",
        ),
        html.Div(
            [
                logo_component(),
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
                html.Div(
                    "Fuente de datos: " + str(data_info),
                    style={
                        "textAlign": "center",
                        "fontSize": "12px",
                        "color": "#666",
                        "marginBottom": "10px",
                    },
                ),
                html.Hr(),
            ]
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.H2("Opciones"),
                        dcc.Tabs(
                            id="tabs",
                            value="tab_anio",
                            children=[
                                dcc.Tab(label="Pérdidas por año", value="tab_anio"),
                                dcc.Tab(
                                    label="Pérdidas por tipología", value="tab_tip"
                                ),
                                dcc.Tab(label="Datos", value="tab_datos"),
                                dcc.Tab(label="Exploratorio", value="tab_explora"),
                                dcc.Tab(label="Inferencia", value="tab_inferencia"),
                                dcc.Tab(label="Modelos", value="tab_modelos"),
                                dcc.Tab(label="Cópulas", value="tab_copulas"),
                                dcc.Tab(label="Galería", value="tab_galeria"),
                            ],
                        ),
                        html.Hr(),
                        html.Label("Filtrar por año:"),
                        dcc.Dropdown(
                            id="dropdown-anio",
                            options=(
                                [
                                    {"label": str(int(x)), "value": int(x)}
                                    for x in sorted(df["ano"].dropna().unique())
                                ]
                                if not df.empty
                                else []
                            ),
                            value=(
                                int(sorted(df["ano"].dropna().unique())[0])
                                if not df.empty
                                else None
                            ),
                            multi=True,
                        ),
                        html.Label("Filtrar por tipología:"),
                        dcc.Dropdown(
                            id="dropdown-tipologia",
                            options=(
                                [
                                    {"label": x, "value": x}
                                    for x in sorted(df["tipologia"].dropna().unique())
                                ]
                                if not df.empty
                                else []
                            ),
                            value=None,
                            multi=True,
                        ),
                        html.Label("Rango de años:"),
                        dcc.RangeSlider(
                            id="slider-anio",
                            min=(int(df["ano"].min()) if not df.empty else 0),
                            max=(int(df["ano"].max()) if not df.empty else 10),
                            step=1,
                            marks=(
                                {
                                    int(a): str(int(a))
                                    for a in sorted(df["ano"].dropna().unique())
                                }
                                if not df.empty
                                else {0: "0", 10: "10"}
                            ),
                            value=(
                                [int(df["ano"].min()), int(df["ano"].max())]
                                if not df.empty
                                else [0, 10]
                            ),
                        ),
                        html.Br(),
                        html.Div(
                            id="alerta-datos",
                            style={"color": "#b00", "fontWeight": "600"}
                            if df.empty
                            else {"display": "none"},
                        ),
                    ],
                    className="Menu",
                ),
                html.Div(id="contenido", className="contenido"),
            ],
            className="cuerpo",
        ),
        html.Footer("Universidad de Costa Rica - Semestre II", className="pie"),
    ],
)


# =========================
# CALLBACKS
# =========================
@callback(Output("contenido", "children"), Input("tabs", "value"))
def render_tab(tab):
    # Pestañas base (mantener nombres y estética)
    if tab == "tab_anio":
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
    if tab == "tab_tip":
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
    if tab == "tab_datos":
        return html.Div(
            [
                html.H3("Datos detallados"),
                dash_table.DataTable(
                    id="tabla-detalles",
                    columns=[{"name": c, "id": c} for c in df.columns],
                    data=df.to_dict("records"),
                    page_size=12,
                    filter_action="native",
                    sort_action="native",
                    export_format="csv",
                    style_table={
                        "overflowX": "auto",
                        "height": "420px",
                        "overflowY": "auto",
                    },
                ),
            ]
        )

    # NUEVAS PESTAÑAS (solo montan lo existente en scripts/imagenes)
    if tab == "tab_explora":
        figs = collect_plotly_figs(prefixes=["explora", "descrip", "eda", "explor"])
        blocks = [
            html.Div(
                [html.H4(name), dcc.Graph(figure=fig)], style={"marginBottom": "18px"}
            )
            for name, fig in figs
        ]
        imgs = find_images_by_keywords(
            [
                "explora",
                "eda",
                "descriptivo",
                "exploratorio",
                "hist",
                "box",
                "violin",
                "kernel",
            ]
        )
        return html.Div(
            [html.H3("Análisis exploratorio"), *blocks, gallery(imgs)],
            style={"padding": "0.5rem"},
        )
    if tab == "tab_inferencia":
        figs = collect_plotly_figs(prefixes=["infer", "anova", "ttest", "ic", "hipo"])
        blocks = [
            html.Div(
                [html.H4(name), dcc.Graph(figure=fig)], style={"marginBottom": "18px"}
            )
            for name, fig in figs
        ]
        imgs = find_images_by_keywords(
            ["infer", "anova", "pvalor", "p-valor", "hipotesis", "intervalo"]
        )
        return html.Div(
            [html.H3("Análisis inferencial"), *blocks, gallery(imgs)],
            style={"padding": "0.5rem"},
        )
    if tab == "tab_modelos":
        figs = collect_plotly_figs(
            prefixes=["model", "regre", "clasif", "arima", "sarima", "xg", "rf", "svm"]
        )
        blocks = [
            html.Div(
                [html.H4(name), dcc.Graph(figure=fig)], style={"marginBottom": "18px"}
            )
            for name, fig in figs
        ]
        imgs = find_images_by_keywords(
            [
                "modelo",
                "model",
                "regre",
                "clasif",
                "arima",
                "sarima",
                "pronost",
                "xg",
                "rf",
                "svm",
            ]
        )
        return html.Div(
            [html.H3("Modelos"), *blocks, gallery(imgs)], style={"padding": "0.5rem"}
        )
    if tab == "tab_copulas":
        imgs = find_images_by_keywords(
            [
                "copula",
                "cópula",
                "empirico",
                "simulado",
                "u1",
                "u2",
                "scatter_empirico_u",
                "comparacion_empirico_simulado",
            ]
        )
        return html.Div(
            [html.H3("Cópulas"), gallery(imgs)], style={"padding": "0.5rem"}
        )
    if tab == "tab_galeria":
        all_imgs = find_images_by_keywords([])
        return html.Div(
            [html.H3("Galería (todas las imágenes)"), gallery(all_imgs)],
            style={"padding": "0.5rem"},
        )

    return html.Div("Sección no disponible.")


@callback(Output("alerta-datos", "children"), Input("tabs", "value"))
def warn_data(tab):
    if df.empty:
        return (
            "No se encontraron datos. Verifica 'datos_crudos.xlsx' en: " + RAW_DATA_DIR
        )
    return ""


@callback(Output("grafico-perdidas-anuales", "figure"), Input("slider-anio", "value"))
def fig_anual(rango):
    filtered = (
        df_perdidas_anuales[
            (df_perdidas_anuales["Año"] >= rango[0])
            & (df_perdidas_anuales["Año"] <= rango[1])
        ]
        if not df_perdidas_anuales.empty
        else pd.DataFrame(columns=["Año", "Pérdidas"])
    )
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=filtered["Año"],
            y=filtered["Pérdidas"],
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


@callback(
    Output("grafico-perdidas-tipologia", "figure"), Input("dropdown-tipologia", "value")
)
def fig_tipologia(tips):
    if df_perdidas_tipologia.empty:
        return go.Figure(
            layout=dict(
                template="simple_white", title="Distribución de Pérdidas por Tipología"
            )
        )
    if not tips or (isinstance(tips, list) and len(tips) == 0):
        filtered = df_perdidas_tipologia
    else:
        if not isinstance(tips, list):
            tips = [tips]
        filtered = df_perdidas_tipologia[df_perdidas_tipologia["Tipología"].isin(tips)]
    fig = px.bar(
        filtered,
        x="Pérdidas",
        y="Tipología",
        orientation="h",
        title="Distribución de Pérdidas por Tipología",
    )
    fig.update_layout(
        template="simple_white",
        xaxis_title="Pérdida en Colones",
        yaxis_title="Tipología",
    )
    fig.update_xaxes(type="log")
    return fig


@callback(Output("tabla-resumen-anual", "data"), Input("slider-anio", "value"))
def tabla_anual(rango):
    filtered = (
        df_perdidas_anuales[
            (df_perdidas_anuales["Año"] >= rango[0])
            & (df_perdidas_anuales["Año"] <= rango[1])
        ]
        if not df_perdidas_anuales.empty
        else pd.DataFrame(columns=["Año", "Pérdidas"])
    )
    if len(filtered) > 0:
        stats = filtered["Pérdidas"].describe().reset_index()
        stats.columns = ["Estadística", "Valor"]
        stats["Valor"] = stats["Valor"].apply(lambda x: f"{x:,.2f}")
        return stats.to_dict("records")
    return []


@callback(
    Output("tabla-resumen-tipologia", "data"), Input("dropdown-tipologia", "value")
)
def tabla_tip(tips):
    if df_perdidas_tipologia.empty:
        return []
    if not tips or (isinstance(tips, list) and len(tips) == 0):
        filtered = df_perdidas_tipologia.copy()
    else:
        if not isinstance(tips, list):
            tips = [tips]
        filtered = df_perdidas_tipologia[
            df_perdidas_tipologia["Tipología"].isin(tips)
        ].copy()
    total = filtered["Pérdidas"].sum()
    filtered["Porcentaje"] = (
        0.0 if total == 0 else (filtered["Pérdidas"] / total * 100).round(2)
    )
    filtered["Pérdidas totales"] = filtered["Pérdidas"].apply(lambda x: f"₡{x:,.2f}")
    filtered["Porcentaje"] = filtered["Porcentaje"].apply(lambda x: f"{x}%")
    return filtered[["Tipología", "Pérdidas totales", "Porcentaje"]].to_dict("records")


if __name__ == "__main__":
    app.run(debug=True)
