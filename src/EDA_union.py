import os
import functools
import pandas as pd

ruta_carpeta = "/home/rali36/Documents/GitHub/Data-analyst-competency-UPQ/Descriptiva_try2/subdatasets_procesados"
columna_compania = "p1_compania"  # <-- Nombre exacto de la columna

archivos_csv = [f for f in os.listdir(ruta_carpeta) if f.endswith('.csv')]
archivos_csv.sort(key=lambda x: int(''.join(filter(str.isdigit, x)) or 0))

# Leer todos los DataFrames
dfs = [pd.read_csv(os.path.join(ruta_carpeta, f)) for f in archivos_csv]

# Unir iterativamente usando la columna de compañía como eje central
df_final = functools.reduce(lambda left, right: pd.merge(left, right, on=columna_compania, how='outer'), dfs)

df_final.to_csv(os.path.join(ruta_carpeta, "resultado_merge_compania.csv"), index=False)