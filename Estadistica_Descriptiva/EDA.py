import pandas as pd
from ydata_profiling import ProfileReport

csv_shot = "../outputs/2024/BASE HISTORICA_SEP-OCT_2024.csv"

df = pd.read_csv (csv_shot)

profile = ProfileReport(df, title="Reporte de Perfilado", explorative=True)
profile.to_file("informe.html")