"""
Gráficas por composición de columnas (no por 'tipo de pregunta'):
  bin -> % de empresas que marcaron cada opción (barras horizontales)
  num -> boxplot / promedio / histograma por opción
  txt -> distribución de respuestas (donut si <=6, barras; apiladas si hay varias columnas)
Excepciones a medida: PERSONALIZADAS["p22"] = lambda df, meta: [("Título", figura), ...]
"""
import pandas as pd
import plotly.express as px

from pipeline import COLUMNA_ID

COLOR = "#1f77b4"
MAX_CATEGORIAS = 15
PERSONALIZADAS = {}


def _etq(meta, col):
    return meta["columnas"][col]["label"]


def _grupos(df, meta):
    g = {"bin": [], "num": [], "txt": []}
    for c, info in meta["columnas"].items():
        if c == COLUMNA_ID or c not in df.columns:
            continue
        if info["kind"] == "bin" and info["label"].startswith("sin nombre") and df[c].sum() == 0:
            continue  # columnas de relleno sin encabezado de opción
        g[info["kind"]].append(c)
    return g


def _fig_bin(df, cols, meta):
    d = pd.DataFrame({
        "opción": [_etq(meta, c) for c in cols],
        "pct": (df[cols].mean() * 100).values,
        "empresas": df[cols].sum().astype(int).values,
    }).sort_values("pct")
    fig = px.bar(d, x="pct", y="opción", orientation="h", hover_data=["empresas"],
                 text=d["pct"].round(1).map("{:.1f}%".format))
    fig.update_traces(marker_color=COLOR, textposition="outside")
    fig.update_xaxes(title="% de empresas")
    fig.update_yaxes(title=None)
    fig.update_layout(height=max(300, 28 * len(d) + 120))
    return fig


def _fig_num(df, cols, meta, ignorar_ceros, modo):
    largo = (df[cols].rename(columns={c: _etq(meta, c) for c in cols})
             .melt(var_name="opción", value_name="valor").dropna())
    if ignorar_ceros:
        largo = largo[largo["valor"] != 0]
    if largo.empty:
        return None
    n = largo["opción"].nunique()
    if modo == "Promedio":
        d = largo.groupby("opción", as_index=False).agg(promedio=("valor", "mean"),
                                                         n=("valor", "size"))
        fig = px.bar(d.sort_values("promedio"), x="promedio", y="opción",
                     orientation="h", hover_data=["n"])
        fig.update_traces(marker_color=COLOR)
    elif modo == "Histograma":
        fig = px.histogram(largo, x="valor", color="opción", barmode="overlay", opacity=0.6)
    else:
        fig = px.box(largo, x="valor", y="opción", orientation="h", points="outliers")
    fig.update_yaxes(title=None) if modo != "Histograma" else None
    fig.update_layout(height=max(320, 40 * n + 140))
    return fig


def _fig_txt(df, cols, meta):
    cols = [c for c in cols if 1 <= df[c].dropna().nunique() <= MAX_CATEGORIAS]
    if not cols:
        return None
    if len(cols) == 1:
        s = (df[cols[0]].dropna().astype(str).value_counts(normalize=True).mul(100)
             .rename("pct").rename_axis("respuesta").reset_index())
        if len(s) <= 6:
            fig = px.pie(s, names="respuesta", values="pct", hole=0.5)
            fig.update_traces(textinfo="label+percent")
            return fig
        fig = px.bar(s.sort_values("pct"), x="pct", y="respuesta", orientation="h")
        fig.update_traces(marker_color=COLOR)
        fig.update_xaxes(title="% de empresas")
        fig.update_layout(height=max(300, 28 * len(s) + 120))
        return fig
    filas = []
    for c in cols:
        vc = df[c].dropna().astype(str).value_counts(normalize=True).mul(100)
        filas += [{"opción": _etq(meta, c), "respuesta": r, "pct": p} for r, p in vc.items()]
    fig = px.bar(pd.DataFrame(filas), x="pct", y="opción", color="respuesta",
                 orientation="h", barmode="stack")
    fig.update_xaxes(title="% de empresas")
    fig.update_layout(height=max(320, 40 * len(cols) + 160))
    return fig


def paneles(df, clave, meta, ignorar_ceros=True, modo_num="Boxplot"):
    """Lista de (título, figura Plotly). Vacía si no hay nada graficable."""
    if df.empty:
        return []
    if clave in PERSONALIZADAS:
        return PERSONALIZADAS[clave](df, meta)
    g = _grupos(df, meta)
    out = []
    try:
        if g["bin"]:
            out.append(("Frecuencia de selección (% de empresas)", _fig_bin(df, g["bin"], meta)))
        if g["num"]:
            out.append(("Valores numéricos", _fig_num(df, g["num"], meta, ignorar_ceros, modo_num)))
        if g["txt"]:
            out.append(("Distribución de respuestas", _fig_txt(df, g["txt"], meta)))
    except Exception as e:  # nunca romper la UI por una pregunta rara
        out.append((f"No se pudo graficar ({type(e).__name__})", None))
    for _, f in out:
        if f is not None:
            f.update_layout(margin=dict(l=10, r=10, t=30, b=10), template="plotly_white")
    return [(t, f) for t, f in out if f is not None]


def tiene_numericas(meta):
    return any(i["kind"] == "num" for c, i in meta["columnas"].items() if c != COLUMNA_ID)