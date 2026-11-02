"""Persistencia: guarda cada sub-dataset en parquet + catalogo.json (sobrevive a recargas)."""
import json
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd

DATA_DIR = Path("data/runs")


def tipo_columna(s: pd.Series) -> str:
    """bin = 0/1 (checkbox) · num = numérica · txt = texto/categórica."""
    if pd.api.types.is_numeric_dtype(s):
        return "bin" if set(s.dropna().unique()) <= {0, 1} else "num"
    return "txt"


def etiqueta(col: str) -> str:
    partes = str(col).split("_", 1)
    return (partes[1] if len(partes) > 1 else str(col)).replace("_", " ")


def guardar_run(subs: dict, titulos: dict, origen: str, progreso=None) -> str:
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:4]
    carpeta = DATA_DIR / run_id
    carpeta.mkdir(parents=True, exist_ok=True)
    catalogo, total = {}, max(len(subs), 1)
    for i, (clave, df) in enumerate(subs.items(), 1):
        archivo = f"{i:04d}.parquet"
        df = df.reset_index(drop=True)
        try:
            df.to_parquet(carpeta / archivo, index=False)
        except Exception:  # columnas de tipos mixtos
            df = df.astype({c: "string" for c in df.select_dtypes("object").columns})
            df.to_parquet(carpeta / archivo, index=False)
        catalogo[clave] = {
            "titulo": titulos.get(clave, clave),
            "archivo": archivo,
            "filas": len(df),
            "columnas": {c: {"kind": tipo_columna(df[c]), "label": etiqueta(c)} for c in df.columns},
        }
        if progreso:
            progreso(i / total, f"Guardando {clave}")
    meta = {"origen": origen, "creado": datetime.now().isoformat(timespec="seconds"),
            "catalogo": catalogo}
    (carpeta / "catalogo.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2),
                                           encoding="utf-8")
    return run_id


def listar_runs() -> list:
    if not DATA_DIR.exists():
        return []
    return sorted((p.name for p in DATA_DIR.iterdir() if (p / "catalogo.json").exists()),
                  reverse=True)


def cargar_meta(run_id: str) -> dict:
    return json.loads((DATA_DIR / run_id / "catalogo.json").read_text(encoding="utf-8"))


def leer_subdataset(run_id: str, archivo: str) -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / run_id / archivo)