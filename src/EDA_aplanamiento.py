import pandas as pd
import re
import unicodedata

def sanitizar_texto(texto):
    """Limpia caracteres especiales, acentos y espacios dobles."""
    if pd.isna(texto):
        return "sin_nombre"
    
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    texto = re.sub(r'[^a-z0-9]+', '_', texto)
    texto = re.sub(r'_+', '_', texto).strip('_')
    
    return texto

def aplanar_encabezados_csv(ruta_csv):
    # CRUCIAL: header=None evita que Pandas se coma la primera fila
    df = pd.read_csv(ruta_csv, header=None, low_memory=False)
    
    # Fila 0 = Preguntas / Fila 1 = Opciones
    fila_preguntas = df.iloc[0].values
    fila_opciones = df.iloc[1].values
    
    nuevos_encabezados = []
    id_pregunta_actual = 0
    
    for preg, opc in zip(fila_preguntas, fila_opciones):
        preg_str = str(preg)
        
        # Si la celda de la fila 0 NO es nula ni empieza con 'Unnamed', es una nueva pregunta
        if pd.notna(preg) and not preg_str.startswith('Unnamed'):
            id_pregunta_actual += 1
            
        opc_limpia = sanitizar_texto(opc)
        nombre_columna = f"p{id_pregunta_actual}_{opc_limpia}"
        nuevos_encabezados.append(nombre_columna)
    
    # Cortar a partir de la fila 2 (donde empiezan las respuestas reales de las empresas/encuestados)
    df_resultado = df.iloc[2:].copy()
    df_resultado.columns = nuevos_encabezados
    df_resultado.reset_index(drop=True, inplace=True)
    
    return df_resultado

# --- PRUEBA DE EJECUCIÓN ---
df_aplanado = aplanar_encabezados_csv("../Descriptiva_try2/SEP-OCT_2024_sin_censura.csv")
df_aplanado.columns.values[0] = 'p1_compania'

print("--- NUEVOS ENCABEZADOS GENERADOS ---")
print(df_aplanado.columns[:10].tolist()) # Ver las primeras 10 columnas

print("\n--- PRIMERA FILA DE DATOS REALES ---")
print(df_aplanado.iloc[0, :5]) # Ver los primeros 5 datos del primer encuestado

ruta_salida = '../Descriptiva_try2/dataset_oficial_aplanado.csv'

df_aplanado.to_csv(ruta_salida, index=False, encoding='utf-8')


