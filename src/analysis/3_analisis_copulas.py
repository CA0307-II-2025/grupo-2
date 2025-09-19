# copulas_borrador.py
# Borrador para ajuste de cópulas a la base datos_crudos.xlsx
# Autor: Dixon Montero Hernández
# Requisitos: pandas, numpy, scipy, matplotlib, statsmodels, copulas

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from copulas.bivariate import (
    GaussianCopula,
    StudentTCopula,
    ClaytonCopula,
    GumbelCopula,
    FrankCopula,
)
import warnings

warnings.filterwarnings("ignore")

# ---------------------------
# 1) Cargar datos
# ---------------------------
file_path = "datos_crudos.xlsx"
df = pd.read_excel(file_path)

# Mostrar info básica
print("Filas totales:", len(df))
print("Columnas disponibles:", df.columns.tolist())
print("Nulos por columna:\n", df.isnull().sum())

# ---------------------------
# 2) Selección y limpieza
# ---------------------------
# Columnas de interés según lo indicado
cols = ["CATEGORÍA", "PROVINCIA", "TOTAL POR TIPOLOGÍA"]
for c in cols:
    if c not in df.columns:
        raise ValueError(f"No se encontró la columna {c} en el archivo.")

df_sel = df[cols].copy()
# Convertir total a numérico y eliminar filas sin total o sin provincia/categoría
df_sel["TOTAL POR TIPOLOGÍA"] = pd.to_numeric(
    df_sel["TOTAL POR TIPOLOGÍA"], errors="coerce"
)
df_sel = df_sel.dropna(
    subset=["CATEGORÍA", "PROVINCIA", "TOTAL POR TIPOLOGÍA"]
).reset_index(drop=True)
print("Filas luego de limpieza:", len(df_sel))

# ---------------------------
# 3) Agregación para obtener variables continuas
#    (sumamos total por cada par CATEGORÍA-PROVINCIA)
# ---------------------------
df_agg = (
    df_sel.groupby(["CATEGORÍA", "PROVINCIA"], dropna=False)["TOTAL POR TIPOLOGÍA"]
    .sum()
    .reset_index()
    .rename(columns={"TOTAL POR TIPOLOGÍA": "total_agr"})
)

print("Filas luego de agregación (pares CATEGORÍA-PROVINCIA):", len(df_agg))
print(df_agg.head())

# ---------------------------
# 4) Construir pares para modelar con cópulas
#    Aquí podemos: (a) estudiar dependencia entre `total_agr` y
#    un codificador ordinal de la CATEGORÍA o PROVINCIA, o
#    (b) elegir dos categorías/provincias específicas y comparar sus totals.
#
#    Estrategia por defecto: crear dos variables continuas usando:
#      - total_agr (como una dimensión)
#      - total_agr_padronizada por categoría (ejemplo) o construir
#        variable 'categoria_code' y 'provincia_code' como ordinales.
#    Para cópulas bivariantes clásicas preferimos dos contínuas:
#      -> GENERAR un conjunto (X,Y) tomando:
#         X = total_agr,
#         Y = total por misma categoría en otra partición (ejemplo: normalizado)
#    Para simplificar: generaremos un par (total_agr, log(total_agr)+ruido)
#    como ejemplo de dos continuas dependientes, además de permitir
#    usar 'categoria_code' para análisis complementario.
# ---------------------------

# Creamos codes ordinales (por si se desean usar como marginals discretas)
df_agg["categoria_code"] = pd.factorize(df_agg["CATEGORÍA"])[0] + 1
df_agg["provincia_code"] = pd.factorize(df_agg["PROVINCIA"])[0] + 1

# Creamos una segunda variable continua relacionada (ejemplo práctico):
# Usaremos la transformación log para la segunda dimensión más un pequeño ruido.
df_agg["total_log"] = np.log1p(df_agg["total_agr"])
df_agg["y_sim"] = df_agg["total_log"] + np.random.normal(
    scale=df_agg["total_log"].std() * 0.1, size=len(df_agg)
)

# Seleccionamos el par (X, Y) para las cópulas
data_for_copula = df_agg[["total_agr", "y_sim"]].copy()


# ---------------------------
# 5) Transformar marginals a U(0,1) (ranks / empírica)
#    - esto produce variables uniformes empíricas U1 y U2 (PIT vía ECDF)
# ---------------------------
def ecdf_transform(x):
    ranks = stats.rankdata(x, method="average")  # rangos
    u = (ranks - 0.5) / len(x)  # transform to (0,1)
    return u


U1 = ecdf_transform(data_for_copula["total_agr"].values)
U2 = ecdf_transform(data_for_copula["y_sim"].values)

U = np.vstack([U1, U2]).T  # matriz Nx2 de uniformes empíricos

# ---------------------------
# 6) Medidas de dependencia
# ---------------------------
kendall_tau = stats.kendalltau(
    data_for_copula["total_agr"], data_for_copula["y_sim"]
).correlation
spearman_rho = stats.spearmanr(
    data_for_copula["total_agr"], data_for_copula["y_sim"]
).correlation
pearson_r = np.corrcoef(data_for_copula["total_agr"], data_for_copula["y_sim"])[0, 1]

print("\nMedidas de dependencia:")
print("Kendall's tau:", kendall_tau)
print("Spearman's rho:", spearman_rho)
print("Pearson r:", pearson_r)

# ---------------------------
# 7) Ajuste de cópulas bivariantes: probamos varias familias
# ---------------------------
# Utilizamos las implementaciones de 'copulas.bivariate' que trabajan con U(0,1) u,v
models = {
    "Gaussian": GaussianCopula(),
    "StudentT": StudentTCopula(),
    "Clayton": ClaytonCopula(),
    "Gumbel": GumbelCopula(),
    "Frank": FrankCopula(),
}

# Ajustar cada cópula usando (u,v) (nota: las clases aceptan datos en [0,1])
results = {}
for name, model in models.items():
    try:
        model.fit(np.column_stack((U1, U2)))
        ll = model.log_likelihood(np.column_stack((U1, U2)))
        # número de parámetros aproximado (usamos 1 o 2 según cópula)
        k = len(model.get_parameters())
        aic = -2 * ll + 2 * k
        results[name] = {
            "model": model,
            "loglik": ll,
            "aic": aic,
            "params": model.get_parameters(),
        }
        print(f"{name}: ll={ll:.3f}, aic={aic:.3f}, params={model.get_parameters()}")
    except Exception as e:
        print(f"Error ajustando {name}: {e}")

# ---------------------------
# 8) Comparación básica por AIC (menor mejor)
# ---------------------------
ranking = sorted(
    [(name, v["aic"]) for name, v in results.items()],
    key=lambda x: x[1] if x[1] is not None else np.inf,
)
print("\nRanking por AIC (menor = mejor):")
for r in ranking:
    print(r)

# ---------------------------
# 9) Gráficos:
#    - Scatter de U1 vs U2 (empírico)
#    - Simulación desde la cópula mejor por AIC y scatter comparativo
#    - Densidad / contorno aproximado (malla) por simulación
# ---------------------------

# Scatter empírico (U)
plt.figure(figsize=(6, 6))
plt.scatter(U1, U2, s=10)
plt.title("Scatter empírico (U1 vs U2) — variables transformadas (ECDF)")
plt.xlabel("U1 (total_agr)")
plt.ylabel("U2 (y_sim)")
plt.grid(True)
plt.tight_layout()
plt.savefig("scatter_empirico_u.png")
print("Guardado: scatter_empirico_u.png")
plt.show()

# Simular desde la mejor cópula (según AIC)
best_name = ranking[0][0]
best_model = results[best_name]["model"]
n_samp = len(U1)
sim = best_model.sample(n_samp)  # devuelve Nx2 en (0,1)

# Scatter de simulación vs empírico
plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.scatter(U1, U2, s=10)
plt.title("Observado (U)")
plt.xlabel("U1")
plt.ylabel("U2")
plt.grid(True)

plt.subplot(1, 2, 2)
plt.scatter(sim[:, 0], sim[:, 1], s=10)
plt.title(f"Simulado desde {best_name}")
plt.xlabel("U1 sim")
plt.ylabel("U2 sim")
plt.grid(True)

plt.tight_layout()
plt.savefig("comparacion_empirico_simulado.png")
print("Guardado: comparacion_empirico_simulado.png")
plt.show()


# ---------------------------
# 10) Prueba de bondad de ajuste sencilla:
#     - Comparamos distribuciones marg. conjuntas con la simulada (en U)
#     - Estadístico Cramer-von Mises entre la CDF empírica y la simulada (aprox).
# ---------------------------
def empirical_cdf_2d(u, v, grid_u, grid_v):
    # calcula la CDF empírica en una malla (grid)
    UU = np.column_stack((u, v))
    G = np.zeros((len(grid_u), len(grid_v)))
    for i, gu in enumerate(grid_u):
        for j, gv in enumerate(grid_v):
            G[i, j] = np.mean((UU[:, 0] <= gu) & (UU[:, 1] <= gv))
    return G


# malla 20x20 en (0,1)
grid_u = np.linspace(0, 1, 21)
grid_v = np.linspace(0, 1, 21)
G_emp = empirical_cdf_2d(U1, U2, grid_u, grid_v)
G_sim = empirical_cdf_2d(sim[:, 0], sim[:, 1], grid_u, grid_v)

cv_stat = np.mean((G_emp - G_sim) ** 2)  # aproximación cuadrática
print(
    f"\nEstadístico aproximado Cramer-von Mises (empírica vs simulada desde {best_name}): {cv_stat:.6f}"
)

# ---------------------------
# 11) Resultados y recomendaciones
# ---------------------------
print("\nMejor modelo según AIC:", best_name)
print("Parámetros del mejor modelo:", results[best_name]["params"])
print("C-V-M aproximado:", cv_stat)

# Guardar data agregada por si quieres inspeccionarla fuera
df_agg.to_csv("datos_agrupados_categoria_provincia.csv", index=False)
print("Datos agregados guardados en datos_agrupados_categoria_provincia.csv")
