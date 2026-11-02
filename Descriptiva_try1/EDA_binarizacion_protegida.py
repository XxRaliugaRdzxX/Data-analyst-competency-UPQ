import pandas as pd

def discriminar_y_binarizar_corregido(df):
    columnas_binarizadas = []
    columnas_protegidas = []
    
    df_resultado = df.copy()
    
    for col in df.columns:
        valores_no_nulos = df[col].dropna()
        cant_unicos = valores_no_nulos.nunique()
        
        nombre_col = str(col).lower()
        
        # Palabras clave que identifican campos de texto libre o identificadores
        es_campo_abierto = any(kw in nombre_col for kw in [
            'compania', 'empresa', 'otro', 'especifique', 
            'comentario', 'nombre', 'open_ended', 'response'
        ])
        
        # CORRECCIÓN AQUÍ: Evaluamos si tiene 0 o 1 valor único [0, 1]
        if cant_unicos in [0, 1] and not es_campo_abierto:
            # Convierte celdas con texto a 1 y celdas vacías (NaN) a 0
            df_resultado[col] = df[col].notna().astype(int)
            columnas_binarizadas.append(col)
        else:
            # Si tiene 2 o más valores distintos O es un campo abierto explícito
            columnas_protegidas.append(col)

    # IMPRESIÓN DE AUDITORÍA
    print(f"--- RESUMEN DE DISCRIMINACIÓN ---")
    print(f"Total columnas procesadas: {len(df.columns)}")
    print(f"Columnas Binarizadas (0/1): {len(columnas_binarizadas)}")
    print(f"Columnas Protegidas (Texto Intacto): {len(columnas_protegidas)}")
    print(f"\nEjemplo de columnas PROTEGIDAS:")
    print(columnas_protegidas[:5])
        
    
    return df_resultado

# --- EJECUCIÓN ---
df_aplanado = pd.read_csv('dataset_aplanado_try2.csv')
df_listo = discriminar_y_binarizar_corregido(df_aplanado)
df_listo.to_csv('dataset_binarizado_perfecto.csv', index=False, encoding='utf-8')