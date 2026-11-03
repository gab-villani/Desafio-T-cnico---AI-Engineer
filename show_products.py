import pandas as pd, pathlib, sys
p = pathlib.Path('data/desafio_tecnico_ai_eng - products.csv')
if not p.exists():
    print('file not found')
    sys.exit()

df = pd.read_csv(p)
print('Columns:', df.columns.tolist())
print('First 10 product names:', df.iloc[:10]['product_name'].tolist())
