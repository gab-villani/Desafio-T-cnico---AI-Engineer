import pandas as pd, pathlib, sys
p = pathlib.Path('data/desafio_tecnico_ai_eng - products.csv')
if not p.exists():
    print('file not found')
    sys.exit()

df = pd.read_csv(p)
print('Number rows', len(df))
print('Sample names:', df['product_name'].head(20).tolist())
