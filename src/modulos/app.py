"""Catch Analytics - Dashboard de análisis de datos.

Ejecutar:  streamlit run app.py
Acceso demo: admin / catch2026  (cambiar en .streamlit/secrets.toml, ver README al final)
Chatbot con IA: define ANTHROPIC_API_KEY (variable de entorno o secrets.toml).
Sin clave, el asistente explica la gráfica con un análisis local.
"""
import hashlib, hmac, io, os, re

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

BLUE, DARK = "#2874B0", "#282828"          # tomados del logo "ch"
SEQ = [BLUE, DARK, "#35B8D6", "#7FB2DC", "#F2A33A", "#8E5AA8", "#5C6B7A"]
PAGES = ["Inicio", "Dashboard", "Reporte", "Asistente AI"]
VIEWS = {"Resumen": ":material/space_dashboard:", "Gráficas": ":material/bar_chart:", "Tabular": ":material/table:"}
KINDS = ["Barras", "Líneas", "Dispersión", "Histograma", "Dona", "Caja", "Correlación"]

st.set_page_config(page_title="Catch Analytics", page_icon=":material/analytics:", layout="wide")
px.defaults.color_discrete_sequence, px.defaults.template = SEQ, "plotly_white"

CSS = "<style>:root{--b:" + BLUE + ";--d:" + DARK + "}" + """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
html,body,.stApp,button,input,textarea{font-family:'Plus Jakarta Sans',system-ui,sans-serif}
.stApp{background:#F4F7FA}
#MainMenu,footer{visibility:hidden}
header[data-testid=stHeader]{background:transparent}
.block-container{padding-top:1.2rem;max-width:1450px}
[data-testid=stSidebar]{background:linear-gradient(180deg,var(--b) 0%,#1D5A8A 100%)}
[data-testid=stSidebar] label p,[data-testid=stSidebar] h3,[data-testid=stSidebar] .stMarkdown p{color:#fff}
[data-testid=stSidebar] [data-testid=stCaptionContainer]{color:#DCEBF7}
[data-testid=stSidebar] .stButton button{width:100%;background:#fff;color:var(--b);border:0;font-weight:600}
[data-testid=stSidebar] div[role=radiogroup] label{padding:.55rem .8rem;border-radius:10px;width:100%}
[data-testid=stSidebar] div[role=radiogroup] label:has(input:checked){background:rgba(255,255,255,.2)}
div[role=radiogroup] label>div:first-child{display:none}
.st-key-topbar{background:#fff;border:1px solid #E3EAF1;border-radius:14px;padding:.4rem 1.2rem;margin-bottom:1rem;box-shadow:0 2px 10px rgba(40,40,40,.05)}
.st-key-topbar div[role=radiogroup]{gap:1.8rem;justify-content:center}
.st-key-topbar div[role=radiogroup] label{padding:.5rem 0;border-bottom:3px solid transparent;color:#5C6B7A;font-weight:600}
.st-key-topbar div[role=radiogroup] label:has(input:checked){border-color:var(--b);color:var(--b)}
.brand{font-size:1.5rem;font-weight:800;color:var(--d);letter-spacing:-.02em}
.brand b{color:var(--b)}
.title{color:var(--b);font-weight:800;font-size:1.7rem;margin:.2rem 0 1rem}
.kpi{background:#fff;border:1px solid #E3EAF1;border-left:5px solid var(--b);border-radius:12px;padding:.9rem 1.1rem;height:100%}
.kpi span{display:block;font-size:.85rem;color:#5C6B7A;font-weight:600}
.kpi h3{margin:.1rem 0 0;color:var(--d);font-size:1.6rem}
.kpi p{margin:.2rem 0 0;color:var(--d)}
.stFormSubmitButton button{width:100%}
</style>"""
SYSTEM = ("Eres un analista de datos que explica gráficas en español claro a personas no técnicas. "
          "Di qué muestra la gráfica, resalta máximos, mínimos y tendencias, y sugiere una acción. "
          "Máximo 150 palabras. No inventes datos que no estén en el contexto.")

# ---------------------------------------------------------------- utilidades
def secret(k):
    try:
        return os.getenv(k) or st.secrets[k]
    except Exception:
        return None


def users():
    base = {"admin": hashlib.sha256(b"catch2026").hexdigest()}   # valores = sha256 de la contraseña
    try:
        base.update(dict(st.secrets["users"]))
    except Exception:
        pass
    return base


@st.cache_data(show_spinner=False)
def load(name, raw):
    b, n = io.BytesIO(raw), name.lower()
    if n.endswith((".xlsx", ".xls")):
        df = pd.read_excel(b)
    elif n.endswith(".json"):
        df = pd.read_json(b)
    else:
        try:
            df = pd.read_csv(b, sep=None, engine="python")
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(raw), sep=None, engine="python", encoding="latin-1")
    df.columns = [str(c).strip() for c in df.columns]
    for c in df.columns:
        if any(k in c.lower() for k in ("fecha", "date")) and not pd.api.types.is_numeric_dtype(df[c]):
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


@st.cache_data
def sample():
    r, n = np.random.default_rng(7), 600
    f = pd.to_datetime("2025-01-01") + pd.to_timedelta(r.integers(0, 365, n), unit="D")
    df = pd.DataFrame({
        "fecha": f,
        "region": r.choice(["Norte", "Centro", "Sur", "Bajío", "Occidente"], n, p=[.2, .25, .15, .25, .15]),
        "producto": r.choice(["Línea A", "Línea B", "Línea C", "Línea D"], n),
        "canal": r.choice(["Distribuidor", "Directo", "En línea"], n, p=[.45, .3, .25]),
        "unidades": r.integers(5, 120, n)})
    df["ventas"] = (df.unidades * r.uniform(80, 260, n)).round(2)
    df["costo"] = (df.ventas * r.uniform(.45, .8, n)).round(2)
    df["mes"] = df.fecha.dt.strftime("%Y-%m")
    return df.sort_values("fecha").reset_index(drop=True)


def insights(df):
    out = [f"El conjunto tiene **{len(df):,} registros** y **{df.shape[1]} columnas**."]
    nul = df.isna().mean()
    out.append(f"La columna con más datos faltantes es **{nul.idxmax()}** ({nul.max():.1%})."
               if nul.max() > 0 else "No hay datos faltantes.")
    num = df.select_dtypes("number")
    if num.shape[1] > 1:
        s = num.corr().abs().unstack()
        s = s[[a < b for a, b in s.index]].dropna()
        if len(s):
            (a, b), v = s.idxmax(), s.max()
            out.append(f"La relación numérica más fuerte es entre **{a}** y **{b}** (correlación {v:.2f}).")
    cat = [c for c in df.columns if c not in num and not pd.api.types.is_datetime64_any_dtype(df[c])]
    if cat and df[cat[0]].notna().any():
        top = df[cat[0]].value_counts(normalize=True)
        out.append(f"En **{cat[0]}**, la categoría dominante es **{top.index[0]}** ({top.iloc[0]:.0%}).")
    return out


def title(t):
    st.markdown(f'<div class="title">{t}</div>', unsafe_allow_html=True)


def kpi(col, label, value):
    col.markdown(f'<div class="kpi"><span>{label}</span><h3>{value}</h3></div>', unsafe_allow_html=True)


def empty():
    st.info("Aún no hay datos. Sube un archivo CSV, Excel o JSON en la barra lateral, o usa los datos de ejemplo.")


# ---------------------------------------------------------------- gráficas
def make_chart(df, kind, x, y, agg):
    yc, A = y, {"Suma": "sum", "Promedio": "mean", "Mediana": "median"}
    if kind in ("Barras", "Líneas", "Dona"):
        if agg == "Conteo" or not y:
            t, yc = df.groupby(x, dropna=False).size().reset_index(name="Conteo"), "Conteo"
        else:
            t = df.groupby(x, dropna=False)[y].agg(A[agg]).reset_index()
        t = t.sort_values(x) if kind == "Líneas" else t.nlargest(25, yc)
        if kind == "Barras":
            fig = px.bar(t, x=x, y=yc, text_auto=".3s")
        elif kind == "Líneas":
            fig = px.line(t, x=x, y=yc, markers=True)
        else:
            fig = px.pie(t, names=x, values=yc, hole=.55)
    elif kind == "Dispersión":
        t = df[[x, y]].dropna()
        fig = px.scatter(t, x=x, y=y, opacity=.7)
    elif kind == "Histograma":
        t = df[[x]]
        fig = px.histogram(t, x=x, nbins=30)
    elif kind == "Caja":
        t = df[[x, y]] if df[x].nunique() <= 15 and x != y else df[[y]]
        fig = px.box(t, x=x if x in t and x != y else None, y=y)
    else:
        t = df.select_dtypes("number").corr().round(2)
        fig = px.imshow(t, text_auto=True, zmin=-1, zmax=1, color_continuous_scale=[DARK, "#FFFFFF", BLUE])
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=440,
                      font=dict(family="Plus Jakarta Sans, sans-serif"))
    return fig, t, yc


def go_chat():
    st.session_state.page = "Asistente AI"
    st.session_state.pending = "Explícame en lenguaje sencillo qué muestra esta gráfica y qué conclusiones puedo sacar."


def charts(df):
    num = df.select_dtypes("number").columns.tolist()
    with st.container(border=True):
        c = st.columns(4)
        kind = c[0].selectbox("Tipo de gráfica", KINDS)
        x = c[1].selectbox("Variable X / categoría", df.columns)
        y = c[2].selectbox("Variable Y / valor", num or [None])
        agg = c[3].selectbox("Agregación", ["Suma", "Promedio", "Mediana", "Conteo"])
    if (kind in ("Dispersión", "Caja") and not y) or (kind == "Correlación" and len(num) < 2):
        return st.warning("Esta gráfica necesita columnas numéricas. Elige otro tipo o carga otro archivo.")
    fig, t, yc = make_chart(df, kind, x, y, agg)
    with st.container(border=True):
        st.plotly_chart(fig)
        st.button("Explicar esta gráfica", on_click=go_chat, type="primary")
    st.session_state.ctx = dict(tipo=kind, x=x, y=yc, agg=agg, data=t, n=len(df),
                                csv=t.head(30).to_csv(index=kind == "Correlación"))


# ---------------------------------------------------------------- chatbot
def local_explain(c):
    if not c:
        return "Todavía no hay una gráfica activa. Ve a **Dashboard → Gráficas**, elige una y vuelve a preguntarme."
    d, y, x = c["data"], c["y"], c["x"]
    head = f"Esta gráfica de **{c['tipo'].lower()}** muestra "
    if c["tipo"] in ("Barras", "Líneas", "Dona") and y in d:
        hi, lo = d.loc[d[y].idxmax()], d.loc[d[y].idxmin()]
        t = (f"**{y}** por **{x}**. El valor más alto es **{hi[x]}** ({hi[y]:,.1f}) y el más bajo **{lo[x]}** "
             f"({lo[y]:,.1f}); el promedio es {d[y].mean():,.1f}.")
        f0, f1 = d[y].iloc[0], d[y].iloc[-1]
        if c["tipo"] == "Líneas" and len(d) > 1 and f0:
            t += f" Del primer al último punto el valor {'sube' if f1 > f0 else 'baja'} {abs(f1 / f0 - 1):.0%}."
        return head + t
    return head + f"los datos de **{x}**. Resumen de lo graficado:\n```\n{d.head(15).to_string()}\n```"


def answer(msgs, ctx):
    key = secret("ANTHROPIC_API_KEY")
    if key:
        try:
            from anthropic import Anthropic
            info = "Sin gráfica activa." if not ctx else (
                f"Tipo: {ctx['tipo']}; X: {ctx['x']}; Y: {ctx['y']} ({ctx['agg']}); registros: {ctx['n']}\n"
                f"Datos graficados (máx. 30 filas):\n{ctx['csv']}")
            r = Anthropic(api_key=key).messages.create(
                model=os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5"), max_tokens=700,
                system=SYSTEM + "\n\nContexto de la gráfica activa:\n" + info, messages=msgs)
            return r.content[0].text
        except Exception as e:
            st.toast(f"Asistente en modo local: {e}")
    return local_explain(ctx)


def asistente():
    title("Asistente AI")
    ctx, chat = st.session_state.get("ctx"), st.session_state.setdefault("chat", [])
    st.caption(f"Gráfica activa: {ctx['tipo']} de {ctx['y']} por {ctx['x']}" if ctx
               else "Sin gráfica activa. Crea una en Dashboard → Gráficas.")
    with st.chat_message("assistant"):
        st.write("Hola, soy tu analista. Puedo traducir la gráfica activa a lenguaje sencillo.")
    for m in chat:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
    q = st.chat_input("Pregunta sobre la gráfica...") or st.session_state.pop("pending", None)
    if q:
        chat.append({"role": "user", "content": q})
        with st.chat_message("user"):
            st.markdown(q)
        with st.chat_message("assistant"):
            with st.spinner("Analizando la gráfica..."):
                a = answer(chat[-7:], ctx)
            st.markdown(a)
        chat.append({"role": "assistant", "content": a})


# ---------------------------------------------------------------- páginas
def inicio(df):
    title(f"Bienvenido, {st.session_state.user}")
    steps = [("Carga tus datos", "Sube un CSV, Excel o JSON desde la barra lateral."),
             ("Explora y filtra", "Grafica en Dashboard y revisa el Reporte automático."),
             ("Pregunta al asistente", "Traduce la gráfica activa a lenguaje sencillo.")]
    for col, (t, d) in zip(st.columns(3), steps):
        col.markdown(f'<div class="kpi"><span>{t}</span><p>{d}</p></div>', unsafe_allow_html=True)
    if df is not None:
        st.success(f"Dataset activo: {st.session_state.name} ({len(df):,} registros tras filtros)")


def dashboard(df):
    if df is None:
        return empty()
    v, num = st.session_state.view, df.select_dtypes("number").columns.tolist()
    title(f"Dashboard · {v}")
    if v == "Resumen":
        c = st.columns(4)
        kpi(c[0], "Registros", f"{len(df):,}")
        kpi(c[1], "Columnas", df.shape[1])
        kpi(c[2], "Variables numéricas", len(num))
        kpi(c[3], "Datos faltantes", f"{df.isna().mean().mean():.1%}")
        st.write("")
        cat = [c for c in df.columns if c not in num and not pd.api.types.is_datetime64_any_dtype(df[c])]
        a, b = st.columns(2)
        if cat:
            with a.container(border=True):
                st.plotly_chart(make_chart(df, "Dona", cat[0], None, "Conteo")[0])
        if num:
            with b.container(border=True):
                st.plotly_chart(make_chart(df, "Histograma", num[0], None, "Suma")[0])
    elif v == "Gráficas":
        charts(df)
    else:
        st.dataframe(df, height=520)
        st.download_button("Descargar datos filtrados (CSV)", df.to_csv(index=False).encode("utf-8-sig"),
                           "datos_filtrados.csv", "text/csv")


def reporte(df):
    title("Reporte general")
    if df is None:
        return empty()
    tips, bold = insights(df), lambda s: re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    with st.container(border=True):
        st.subheader("Hallazgos clave")
        for t in tips:
            st.markdown("- " + t)
    a, b = st.columns(2)
    a.subheader("Estadística descriptiva")
    a.dataframe(df.describe().round(2).T)
    b.subheader("Calidad de datos")
    b.dataframe(pd.DataFrame({"Tipo": df.dtypes.astype(str), "Nulos %": (df.isna().mean() * 100).round(1),
                              "Únicos": df.nunique()}))
    html = ("<html><head><meta charset='utf-8'><style>body{font-family:sans-serif;max-width:900px;margin:2rem auto;"
            f"color:{DARK}}}h1,h2{{color:{BLUE}}}td,th{{border:1px solid #ddd;padding:4px 8px}}table{{border-collapse:collapse}}"
            f"</style></head><body><h1>Reporte · {st.session_state.name}</h1><ul>"
            + "".join(f"<li>{bold(t)}</li>" for t in tips) + "</ul><h2>Estadística descriptiva</h2>"
            + df.describe().round(2).T.to_html() + "</body></html>")
    st.download_button("Descargar reporte (HTML)", html.encode("utf-8"), "reporte.html", "text/html")


# ---------------------------------------------------------------- estructura
def filters(raw):
    s, df = st.sidebar, raw
    s.markdown("### Filtros")
    for c in s.multiselect("Columnas a filtrar", raw.columns):
        col = df[c]
        if pd.api.types.is_numeric_dtype(col):
            lo, hi = float(col.min()), float(col.max())
            if lo < hi:
                a, b = s.slider(c, lo, hi, (lo, hi))
                df = df[col.between(a, b)]
        elif pd.api.types.is_datetime64_any_dtype(col):
            r = s.date_input(c, (col.min().date(), col.max().date()))
            if len(r) == 2:
                df = df[col.dt.date.between(*r)]
        else:
            sel = s.multiselect(c, sorted(col.dropna().astype(str).unique()))
            if sel:
                df = df[col.astype(str).isin(sel)]
    s.caption(f"{len(df):,} de {len(raw):,} registros")
    return df


def sidebar():
    s = st.sidebar
    s.markdown("### Catch Analytics")
    s.radio("Secciones", list(VIEWS), key="view", format_func=lambda v: f"{VIEWS[v]} {v}")
    s.markdown("### Datos")
    f = s.file_uploader("Archivo", type=["csv", "xlsx", "xls", "json"], label_visibility="collapsed")
    if f and st.session_state.get("sig") != (f.name, f.size):
        try:
            st.session_state.update(raw=load(f.name, f.getvalue()), name=f.name, sig=(f.name, f.size))
        except Exception as e:
            s.error(f"No se pudo leer el archivo: {e}")
    if s.button("Usar datos de ejemplo"):
        st.session_state.update(raw=sample(), name="ejemplo_ventas.csv")
    raw = st.session_state.get("raw")
    return None if raw is None else filters(raw)


def topbar():
    with st.container(key="topbar"):
        a, b, c = st.columns([1.4, 3.6, 1.6], vertical_alignment="center")
        a.markdown('<div class="brand"><b>C</b>atch Analytics</div>', unsafe_allow_html=True)
        b.radio("Navegación", PAGES, key="page", horizontal=True, label_visibility="collapsed")
        c1, c2 = c.columns(2, vertical_alignment="center")
        c1.markdown(f"<div style='text-align:right;font-weight:600'>{st.session_state.user}</div>", unsafe_allow_html=True)
        c2.button("Cerrar sesión", on_click=st.session_state.clear)


def login():
    st.markdown(CSS, unsafe_allow_html=True)
    _, c, _ = st.columns([1, 1.1, 1])
    with c:
        st.write("")
        st.markdown('<div class="brand" style="font-size:2.4rem;text-align:center"><b>C</b>atch Analytics</div>',
                    unsafe_allow_html=True)
        st.caption("Inicia sesión para acceder a tus tableros.")
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            ok = st.form_submit_button("Iniciar sesión", type="primary")
        if ok:
            h = users().get(u, "")
            if h and hmac.compare_digest(h, hashlib.sha256(p.encode()).hexdigest()):
                st.session_state.user = u
                st.rerun()
            st.error("Usuario o contraseña incorrectos.")


def main():
    if "user" not in st.session_state:
        return login()
    st.markdown(CSS, unsafe_allow_html=True)
    topbar()
    df, p = sidebar(), st.session_state.page
    if p == "Inicio":
        inicio(df)
    elif p == "Dashboard":
        dashboard(df)
    elif p == "Reporte":
        reporte(df)
    else:
        asistente()


main()