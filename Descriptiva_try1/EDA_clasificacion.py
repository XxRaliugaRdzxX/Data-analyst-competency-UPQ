import pandas as pd
import numpy as np

def clasificar_y_transformar_dataset(df):
    columnas_binarizadas = []
    columnas_numericas = []
    columnas_texto = []
    
    df_resultado = df.copy()
    
    for col in df.columns:
        valores_originales = df[col]
        valores_no_nulos = valores_originales.dropna()
        
        # Si la columna está completamente vacía (puros NaNs), la tratamos como binarizable nula
        if valores_no_nulos.empty:
            df_resultado[col] = 0
            columnas_binarizadas.append(col)
            continue

        cant_unicos = valores_no_nulos.nunique()
        nombre_col = str(col).lower()
        
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
        # Convertimos a string, cambiamos comas por puntos y forzamos la conversión a número
        intento_numerico = pd.to_numeric(
            valores_originales.astype(str).str.replace(',', '.', regex=False), 
            errors='coerce' # Si encuentra una letra, pondrá NaN
        )
        
        # Comparamos cuántos datos válidos había originalmente vs cuántos sobrevivieron a la conversión numérica
        # Si la cantidad es igual (o muy parecida, digamos >95% de éxito), significa que es una columna numérica
        tasa_exito = intento_numerico.notna().sum() / len(valores_no_nulos)
        
        if tasa_exito > 0.95: 
            # Es numérica. Aplicamos el cambio al dataset final
            df_resultado[col] = intento_numerico
            columnas_numericas.append(col)
        
        # 3. SI FALLA LAS DOS ANTERIORES, ES TEXTO (Protegida)
        else:
            # Aquí caerán "Excelente", "Buena", "COMPAÑIA 1", etc.
            columnas_texto.append(col)

    # REPORTE DE AUDITORÍA
    print(f"--- RESUMEN DE PROCESAMIENTO ---")
    print(f"Binarizadas (0 y 1): {len(columnas_binarizadas)} columnas")
    print(f"Numéricas Continuas/Discretas (Int/Float): {len(columnas_numericas)} columnas")
    print(f"Texto Protegido (Categóricas/Abiertas): {len(columnas_texto)} columnas\n")
    
    print(f"Ejemplo Numéricas detectadas: {columnas_numericas[:5]}")
    
    return df_resultado

# --- EJECUCIÓN ---
# Asumiendo que df_aplanado es tu dataset después de la Fase 1
df_aplanado = pd.read_csv('dataset_aplanado_try3.csv')
df_tipificado = clasificar_y_transformar_dataset(df_aplanado)

df_tipificado.to_csv('dataset_estructurado.csv', index=False, encoding='utf-8')




