import pandas as pd

dat_cen = 'datos_censurados_sep_oct_2024.csv'
dat_lim = 'SEP-OCT_2024_LIM.csv'

csv_shot = "../outputs/2024/BASE HISTORICA_SEP-OCT_2024.csv"

df = pd.read_csv(csv_shot, low_memory=False)

print(f"Dimensiones: {df.shape[0]:,} filas × {df.shape[1]} columnas")

atributos = df.columns.tolist()

#print(atributos)
print(len(atributos))

columnas_con_guion = [col for col in df.columns if (df[col] == '-').any()]
columnas_limpias = [col for col in df.columns if col not in columnas_con_guion]

print("Columnas censuradas (contienen '-'):")
print(len(columnas_con_guion))

print("\nColumnas limpias a conservar:")
print(len(columnas_limpias))

df_con_datos_censurados = df[columnas_con_guion]
df_con_datos_utiles = df[columnas_limpias]

df_con_datos_censurados.to_csv(dat_cen, index=False, encoding='utf-8')
df_con_datos_utiles.to_csv(dat_lim, index=False, encoding='utf-8')