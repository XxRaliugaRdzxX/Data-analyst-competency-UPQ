import pandas as pd
import numpy as np

csv_shot = "SEP-OCT_2024_sin_censura.csv"

df = pd.read_csv(csv_shot, low_memory=False)

#print(f"Dimensiones: {df.shape[0]:,} filas × {df.shape[1]} columnas")

#df_limpio = df.replace(r'^\s*$', np.nan, regex=True)

print(len(df.columns))
k = len(df.columns)
#print(len(df_limpio.columns))
atributos = list(df.columns)

columnas_unnamed = [col for col in atributos if str(col).startswith('Unnamed:')]
columnas_validas = [col for col in atributos if not str(col).startswith('Unnamed:')]

print(len(columnas_unnamed))
d = len(columnas_unnamed)

dif = k - d
print("\nLa cantidad de atributos utilies (NUMERO DE PREGUNTAS) [ZONA DE MUESTREO REAL] es de:", dif)

df_sin_unnamed = df.drop(columns=columnas_unnamed)

ruta_salida = 'dataset_sin_censura_unnamed.csv'

df_sin_unnamed.to_csv(ruta_salida, index=False, encoding='utf-8')


'''
atributos_vacios = []
atributos_info = []

for col in atributos:
    # Contamos la cantidad de registros no nulos en la columna
    conteo_datos = df_limpio[col].dropna().count()
    
    if conteo_datos == 1:
        atributos_vacios.append(col)
    else:
        atributos_info.append(col)

# 3. Mostrar conteo detallado
print(f"Columnas TOTALMENTE VACÍAS ({len(atributos_vacios)}):")

print(f"\nColumnas CON AL MENOS UN DATO O MÁS ({len(atributos_info)}):")
'''