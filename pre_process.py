import pandas as pd
from langdetect import detect
import os

cidades = ['Amir']
for cidade in cidades:

    #hotel = pd.read_csv(os.path.join(cidade, 'hoteis.csv'), dtype={"latitude": "string", "longitude": "string"}).drop_duplicates('hotel_id')
    #restaurantes = pd.read_csv(os.path.join(cidade, 'restaurantes.csv'), dtype={"latitude": "string", "longitude": "string"}).drop_duplicates()
    atracoes = pd.read_csv(os.path.join(cidade, 'museus.csv'), dtype={"latitude": "string", "longitude": "string"}).drop_duplicates("atracao_id")

    #aval_hotel = pd.read_csv(os.path.join(cidade, 'avaliacoes-hoteis.csv'), dtype={"latitude": "string", "longitude": "string"}).drop_duplicates()
    #aval_rest = pd.read_csv(os.path.join(cidade, 'avaliacoes-restaurantes.csv'), dtype={"latitude": "string", "longitude": "string"})
    #aval_rest = aval_rest.drop_duplicates(aval_rest.columns[:-2])
    aval_atr = pd.read_csv(os.path.join(cidade, 'avaliacoes-museus.csv'), dtype={"latitude": "string", "longitude": "string"}).drop_duplicates(["usuario", "conteudo"])

    print('Detectando idiomas...')
    #aval_hotel['idioma'] = aval_hotel.apply(lambda row: detect(row['conteudo']), axis=1)
    #aval_rest['idioma'] = aval_rest.apply(lambda row: detect(row['conteudo']), axis=1)
    #aval_atr['idioma'] = aval_atr.apply(lambda row: detect(row['conteudo']), axis=1)

    #hotel.to_csv(os.path.join(cidade, 'hoteis.csv'), index=False)
    #restaurantes.to_csv(os.path.join(cidade, 'restaurantes.csv'), index=False)
    atracoes.to_csv(os.path.join(cidade, 'museus.csv'), index=False)

    #aval_hotel.to_csv(os.path.join(cidade, 'avaliacoes-hoteis.csv'), index=False)
    #aval_rest.to_csv(os.path.join(cidade, 'avaliacoes-restaurantes.csv'), index=False)
    aval_atr.to_csv(os.path.join(cidade, 'avaliacoes-museus.csv'), index=False)
