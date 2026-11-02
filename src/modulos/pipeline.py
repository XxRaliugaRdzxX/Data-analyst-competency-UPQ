"""
Pipeline completo: CSV crudo (2 filas de encabezado) -> sub-datasets limpios por pregunta.
Es tu código refactorizado en funciones (sin ejecutarse al importar).
`clasificar_y_transformar_dataset` está SIN CAMBIOS en su lógica.
Mejoras: (1) conserva el texto de cada pregunta (fila 0) como título,
(2) ordena p1, p2, p3... numéricamente, (3) evita encabezados duplicados.
"""
import re
import unicodedata

import pandas as pd

COLUMNA_ID = "p1_compania"
PREGUNTAS_MEDIANA = {"p14", "p15", "p16", "p17", "p22", "p23", "p24"}


def sanitizar_texto(texto):
    """Limpia caracteres especiales, acentos y espacios dobles."""
    if pd.isna(texto):
        return "sin_nombre"
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ASCII", "ignore").decode("utf-8")
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    return re.sub(r"_+", "_", texto).strip("_")


def leer_crudo(archivo) -> pd.DataFrame:
    nombre = str(getattr(archivo, "name", archivo)).lower()
    if nombre.endswith((".xlsx", ".xls")):
        return pd.read_excel(archivo, header=None)
    try:  # header=None: no perder la primera fila
        return pd.read_csv(archivo, header=None, low_memory=False)
    except UnicodeDecodeError:
        if hasattr(archivo, "seek"):
            archivo.seek(0)
        return pd.read_csv(archivo, header=None, low_memory=False, encoding="latin-1")


def aplanar_encabezados(df: pd.DataFrame):
    """Fila 0 = preguntas, fila 1 = opciones. Devuelve (df_aplanado, {pN: texto_pregunta})."""
    encabezados, titulos, usados = [], {}, {}
    id_actual = 0
    for preg, opc in zip(df.iloc[0].values, df.iloc[1].values):
        if pd.notna(preg) and not str(preg).startswith("Unnamed"):
            id_actual += 1
            titulos[f"p{id_actual}"] = str(preg).strip()
        nombre = f"p{id_actual}_{sanitizar_texto(opc)}"
        usados[nombre] = usados.get(nombre, 0) + 1
        if usados[nombre] > 1:
            nombre = f"{nombre}_{usados[nombre]}"
        encabezados.append(nombre)
    res = df.iloc[2:].copy()
    res.columns = encabezados
    res.reset_index(drop=True, inplace=True)
    res = res.rename(columns={encabezados[0]: COLUMNA_ID})
    return res, titulos


def particionar(df: pd.DataFrame, columna_id: str = COLUMNA_ID) -> dict:
    prefijos = {m.group(1) for c in df.columns if (m := re.match(r"^(p\d+)_", c))}
    out = {}
    for p in sorted(prefijos, key=lambda x: int(x[1:])):
        cols = [c for c in df.columns if c.startswith(f"{p}_")]
        if columna_id not in cols:
            cols.insert(0, columna_id)
        out[p] = df[cols].copy()
    return out


def clasificar_y_transformar_dataset(df, nombre_pregunta, estrategia_nulos="cero"):
    columnas_binarizadas, columnas_numericas, columnas_texto = [], [], []
    df_resultado = df.copy()

    for col in df.columns:
        valores_originales = df[col]
        valores_no_nulos = valores_originales.dropna()

        if valores_no_nulos.empty:
            df_resultado[col] = 0
            columnas_binarizadas.append(col)
            continue

        cant_unicos = valores_no_nulos.nunique()
        nombre_col = str(col).lower()

        es_campo_abierto_por_nombre = any(kw in nombre_col for kw in [
            "compania", "empresa", "otro", "especifique",
            "comentario", "nombre", "open_ended", "response"
        ])

        # 1. BINARIZABLE (checkbox)
        if cant_unicos in [0, 1] and not es_campo_abierto_por_nombre:
            df_resultado[col] = df[col].notna().astype(int)
            columnas_binarizadas.append(col)
            continue

        # 2. CONTINUA / NUMÉRICA
        intento_numerico = pd.to_numeric(
            valores_originales.astype(str).str.replace(",", ".", regex=False),
            errors="coerce"
        )
        tasa_exito = intento_numerico.notna().sum() / len(valores_no_nulos) if len(valores_no_nulos) > 0 else 0

        if tasa_exito > 0.95:
            if estrategia_nulos == "cero":
                df_resultado[col] = intento_numerico.fillna(0)
            elif estrategia_nulos == "mediana":
                df_resultado[col] = intento_numerico.fillna(intento_numerico.median())
            else:
                df_resultado[col] = intento_numerico
            columnas_numericas.append(col)
        # 3. TEXTO (protegida)
        else:
            columnas_texto.append(col)

    if columnas_numericas or columnas_binarizadas:
        print(f"[{nombre_pregunta}] Binarizadas: {len(columnas_binarizadas)} | "
              f"Numéricas: {len(columnas_numericas)} | Texto: {len(columnas_texto)}")
    return df_resultado


def procesar(archivo, progreso=None):
    """Punto de entrada para el dashboard. Devuelve ({pN: df_limpio}, {pN: título})."""
    df, titulos = aplanar_encabezados(leer_crudo(archivo))
    subs = particionar(df)
    limpio, total = {}, max(len(subs), 1)
    for i, (p, sub) in enumerate(subs.items(), 1):
        estrategia = "mediana" if p in PREGUNTAS_MEDIANA else "cero"
        limpio[p] = clasificar_y_transformar_dataset(sub, p, estrategia)
        if progreso:
            progreso(i / total, f"Procesando {p}")
    return limpio, titulos