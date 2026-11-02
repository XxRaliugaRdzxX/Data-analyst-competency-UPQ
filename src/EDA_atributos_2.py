import pandas as pd
import numpy as np

csv_shot = "dataset_sin_censura_unnamed.csv"

df = pd.read_csv(csv_shot, low_memory=False)

extract = df.columns

rut = 'atributos.csv'

pd.Series(extract, name="Atributo").to_csv(rut, index=False, encoding='utf-8')
