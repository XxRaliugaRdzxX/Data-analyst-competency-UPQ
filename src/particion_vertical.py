import pandas as pd
import re
import numpy as np
import os


df_aplanado = pd.read_csv('../Descriptiva_try2/dataset_oficial_aplanado.csv')

# Asumimos que tu dataframe se llama df_aplanado
columna_id = 'p1_compania'

# 1. Extraer todos los prefijos únicos (p1, p2, p3... p166) usando una expresión regular
# Esto busca patrones como "p1_", "p22_", "p116_" al inicio del nombre de la columna
prefijos = set()
for col in df_aplanado.columns:
    match = re.match(r'^(p\d+)_', col)
    if match:
        prefijos.add(match.group(1)) # Guarda 'p1', 'p2', etc.

# 2. Crear un DICCIONARIO para almacenar todos los sub-datasets
diccionario_preguntas = {}

# 3. Llenar el diccionario iterando sobre los prefijos
for p in prefijos:
    # Filtramos las columnas que empiezan con el prefijo actual (ej. 'p3_')
    columnas_de_pregunta = [col for col in df_aplanado.columns if col.startswith(f'{p}_')]
    
    # Aseguramos que la columna ID siempre esté en el sub-dataset, si no es la misma pregunta 1
    if columna_id not in columnas_de_pregunta:
        columnas_de_pregunta.insert(0, columna_id)
        
    # Guardamos el sub-dataset en el diccionario usando el prefijo como llave
    diccionario_preguntas[p] = df_aplanado[columnas_de_pregunta].copy()

#  print(f"Se generaron {len(diccionario_preguntas)} sub-datasets.")

print(diccionario_preguntas['p3'])



# Accedes al sub-dataset de 'p1' desde tu diccionario y lo guardas en CSV
#diccionario_preguntas['p13'].to_csv('subdataset_p1.csv', index=False, encoding='utf-8')

#print("¡Archivo subdataset_p1.csv guardado con éxito!")



def clasificar_y_transformar_dataset(df, nombre_pregunta, estrategia_nulos='cero'):
    columnas_binarizadas = []
    columnas_numericas = []
    columnas_texto = []
    
    df_resultado = df.copy()
    
    for col in df.columns:
        valores_originales = df[col]
        valores_no_nulos = valores_originales.dropna()
        
        # Si la columna está completamente vacía (puros NaNs)
        if valores_no_nulos.empty:
            df_resultado[col] = 0
            columnas_binarizadas.append(col)
            continue

        cant_unicos = valores_no_nulos.nunique()
        nombre_col = str(col).lower()
        
        # Protección de campos abiertos y el ID principal
        es_campo_abierto_por_nombre = any(kw in nombre_col for kw in [
            'compania', 'empresa', 'otro', 'especifique', 
            'comentario', 'nombre', 'open_ended', 'response'
        ])
        
        # 1. EVALUAR SI ES BINARIZABLE (Checkbox)
        if cant_unicos in [0, 1] and not es_campo_abierto_por_nombre:
            df_resultado[col] = df[col].notna().astype(int)
            columnas_binarizadas.append(col)
            continue
            
        # 2. EVALUAR SI ES CONTINUA/NUMÉRICA
        intento_numerico = pd.to_numeric(
            valores_originales.astype(str).str.replace(',', '.', regex=False), 
            errors='coerce'
        )
        
        tasa_exito = intento_numerico.notna().sum() / len(valores_no_nulos) if len(valores_no_nulos) > 0 else 0
        
        if tasa_exito > 0.95: 
            # Imputación de NaNs para evitar sesgos en el EDA
            if estrategia_nulos == 'cero':
                df_resultado[col] = intento_numerico.fillna(0)
            elif estrategia_nulos == 'mediana':
                df_resultado[col] = intento_numerico.fillna(intento_numerico.median())
            else:
                df_resultado[col] = intento_numerico
                
            columnas_numericas.append(col)
        
        # 3. TEXTO (Protegida)
        else:
            columnas_texto.append(col)

    # Imprimir un mini-reporte solo si detectó columnas numéricas o binarizadas
    if columnas_numericas or columnas_binarizadas:
        print(f"[{nombre_pregunta}] Binarizadas: {len(columnas_binarizadas)} | Numéricas: {len(columnas_numericas)} | Texto: {len(columnas_texto)}")
    
    return df_resultado

# --- EJECUCIÓN MASIVA SOBRE EL DICCIONARIO ---
# Asumiendo que 'diccionario_preguntas' ya existe en tu entorno tras la partición vertical

diccionario_limpio = {}
carpeta_destino = '../Descriptiva_try2/subdatasets_procesados'
os.makedirs(carpeta_destino, exist_ok=True)

print("--- INICIANDO PROCESAMIENTO MASIVO ---")

for pregunta, df_sub in diccionario_preguntas.items():
    # Podemos aplicar lógicas distintas según la pregunta si lo deseamos. 
    # Por defecto usaremos 'cero', pero puedes cambiar a 'mediana' para preguntas salariales.
    estrategia = 'mediana' if pregunta in ['p14', 'p15', 'p16', 'p17', 'p22', 'p23', 'p24'] else 'cero'
    
    # Aplicamos la función a cada dataframe
    df_procesado = clasificar_y_transformar_dataset(df_sub, nombre_pregunta=pregunta, estrategia_nulos=estrategia)
    
    # Guardamos en el nuevo diccionario
    diccionario_limpio[pregunta] = df_procesado
    
    # (Opcional) Exportamos el resultado limpio a CSV
    ruta_archivo = os.path.join(carpeta_destino, f'dataset_{pregunta}_limpio.csv')
    df_procesado.to_csv(ruta_archivo, index=False, encoding='utf-8')

print(f"\nProcesamiento completado. {len(diccionario_limpio)} sub-datasets limpios y exportados.")