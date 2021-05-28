import pandas as pd
from langdetect import detect
import os

cidades = ['Ilhas Galápagos']
for cidade in cidades:

    hotel = pd.read_csv(os.path.join(cidade, 'hoteis.csv'), float_precision=None).drop_duplicates('hotel_id')
    restaurantes = pd.read_csv(os.path.join(cidade, 'restaurantes.csv'), float_precision=None).drop_duplicates()
    atracoes = pd.read_csv(os.path.join(cidade, 'atracoes.csv'), float_precision=None).drop_duplicates()

    aval_hotel = pd.read_csv(os.path.join(cidade, 'avaliacoes-hoteis.csv')).drop_duplicates()
    aval_rest = pd.read_csv(os.path.join(cidade, 'avaliacoes-restaurantes.csv'))
    aval_rest = aval_rest.drop_duplicates(aval_rest.columns[:-2])
    aval_atr = pd.read_csv(os.path.join(cidade, 'avaliacoes-atracoes.csv')).drop_duplicates()

    print('Detectando idiomas...')
    aval_hotel['idioma'] = aval_hotel.apply(lambda row: detect(row['conteudo']), axis=1)
    aval_rest['idioma'] = aval_rest.apply(lambda row: detect(row['conteudo']), axis=1)
    aval_atr['idioma'] = aval_atr.apply(lambda row: detect(row['conteudo']), axis=1)

    hotel.to_csv(os.path.join(cidade, 'hoteis.csv'), index=False)
    restaurantes.to_csv(os.path.join(cidade, 'restaurantes.csv'), index=False)
    atracoes.to_csv(os.path.join(cidade, 'atracoes.csv'), index=False)

    aval_hotel.to_csv(os.path.join(cidade, 'avaliacoes-hoteis.csv'), index=False)
    aval_rest.to_csv(os.path.join(cidade, 'avaliacoes-restaurantes.csv'), index=False)
    aval_atr.to_csv(os.path.join(cidade, 'avaliacoes-atracoes.csv'), index=False)
