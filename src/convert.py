import pandas as pd
import os

excel = pd.ExcelFile('../data/BASE HISTORICA.xlsx')
print(excel.sheet_names)

for sheet_name in excel.sheet_names:
    df = pd.read_excel(excel, sheet_name=sheet_name)
    
    output_name = f"../outputs/BASE HISTORICA_{sheet_name}.csv"
    
    df.to_csv(output_name, index=False, encoding='utf-8')
    print(f"Convertida la hoja '{sheet_name}' -> {output_name}")