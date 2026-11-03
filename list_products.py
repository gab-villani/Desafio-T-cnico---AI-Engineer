import pandas as pd, pathlib, sys
p = pathlib.Path('data/desafio_tecnico_ai_eng - products.csv')
print('exists', p.exists())
if p.exists():
    df = pd.read_csv(p)
    print(df['product_name'].head(20).tolist())
