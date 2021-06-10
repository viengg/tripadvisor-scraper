# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial, reduce
import os
import dateparser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime
import pandas as pd
import math
from webdriver_manager.chrome import ChromeDriverManager


#session = requests.Session()
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36'}
language = '.br'
trip_url = 'https://www.tripadvisor.com' + language

LANGUAGES_TO_COLLECT = ['.br', ''] # '' significa para coletar em ingles
REQUEST_DELAY = 30
COLLECT_UNTIL = 2015
ONLY_REVIEWS = False
UPDATE_REVIEWS = False
TOO_MUCH_REVIEW_PAGES = 50
NUM_THREADS_FOR_REVIEW = 8
NUM_THREADS_FOR_PLACE = 2

def get_soup(url):
    time.sleep(REQUEST_DELAY)
    
    max_num_tries = 3
    while max_num_tries > 0:
        try:
            r = requests.get(url, headers=headers)
            break
        except:
            time.sleep(5*60)
            max_num_tries -= 1

    soup = BeautifulSoup(r.text, 'lxml')
    return soup

def parse_date(date):
    date_parsed = str(dateparser.parse(date))
    return date_parsed.split()[0]

def get_driver_selenium(url):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('disable-infobars')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-gpu')

    max_num_tries = 3
    while max_num_tries > 0:
        try:
            wd = webdriver.Chrome(options=chrome_options)
            wd.get(url)
            time.sleep(REQUEST_DELAY)
            break
        except:
            time.sleep(5*60)
            max_num_tries -= 1
    return wd

#A partir de um link de hotel, entra na pagina do hotel em questao
#e extrai seus dados
def get_hotel_data(city_name, comentarios_flag, hoteis_coletados, entry_link):
    entry_url = trip_url + entry_link
    driver = get_driver_selenium(entry_url)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    #soup = get_soup(entry_url)

    cidade = soup.find('a', id='global-nav-tourism').string
    #if not cidade.replace(' ','') == city_name.replace(' ', ''):
    #    return {}
    
    hotel_id = entry_link.split("-")[2][1:]
    if hoteis_coletados is not None and not UPDATE_REVIEWS:
        if int(hotel_id) in hoteis_coletados['hotel_id'].values:
            return {}

    try:
        nome = "\"" + soup.find(id="HEADING").string.strip() + "\""
    except:
        nome = 'indef'
    try:
        preco = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "bookableOffer")))
        preco = preco.get_attribute('data-pernight')
        #preco = soup.find(class_='bookableOffer')['data-pernight']
    except:
        preco = 'indef'
    time.sleep(3)
    driver.quit()
    try:
        endereco = '\"' + soup.find(class_='_3ErVArsu jke2_wbp').string + '\"'
    except:
        endereco = "indef"
    try:
        qtd_avaliacoes = soup.find("span", class_='_33O9dg0j').string.split()[0].replace('.','')
    except:
        qtd_avaliacoes = "0"
    try:
        nota = soup.find("span", class_="_3cjYfwwQ").string.replace(",", ".")
    except:
        nota = "indef"
    try:
        nota_pedestres = soup.find("span", class_="oPMurIUj _1iwDIdby").string
    except:
        nota_pedestres = "indef"
    try:
        restaurantes_perto = soup.find("span", class_="oPMurIUj TrfXbt7b").string
    except:
        restaurantes_perto = "indef"
    try:
        atracoes_perto = soup.find("span", class_="oPMurIUj _1WE0iyL_").string
    except:
        atracoes_perto = "indef"
    try:
        categoria = soup.find("svg", class_="_2aZlo29m")['title'].split()[0].replace(",", ".")
    except:
        categoria = "indef"
    qtd_quartos = soup.find(attrs={'class':'_2t2gK1hs', 'data-tab':'TABS_ABOUT'}).findAll(class_="_1NHwuRzF")[-1].string
    if qtd_quartos is None:
        qtd_quartos = "indef"
        
    tipo = get_type_by_name(nome, ['Hotel', 'Pousada', 'Hostel', 'Chale'])

    try:
        # So precisa acessar json se for pra escrever os hoteis
        if not ONLY_REVIEWS:
            api_url = 'https://www.tripadvisor.com.br/data/1.0/mapsEnrichment/hotel/{}?rn=1&rc=Hotel_Review&guestInfo=1_2&placementName=Hotel_Review_MapDetail_Anchor&currency=BRL'.format(hotel_id)
            api_json = requests.get(api_url).json()
        else:
            api_json = {}
        coords = api_json['hotels'][0]['location']['geoPoint']
        lat = str(coords['latitude'])
        lon = str(coords['longitude'])
    except:
        lat = "indef"
        lon = "indef"
    if qtd_avaliacoes != '0' and comentarios_flag == 's':
        if UPDATE_REVIEWS:
            comentarios = atualiza_reviews(city_name, nome, hotel_id, 'hotel-review', entry_link, get_hotel_review_data, get_hotel_review_cards)
        else:
            comentarios = coleta_reviews(nome, hotel_id, 'hotel-review', entry_link, get_hotel_review_data, get_hotel_review_cards)
        write_to_file(os.path.join(city_name, 'avaliacoes-hoteis.csv'), comentarios)
    data ={
        'hotel_id': hotel_id,
        'nome': nome,
        'endereco': endereco,
        'cidade': cidade,
        'preco': preco,
        'tipo': tipo,
        'qtd_quartos': qtd_quartos,
        'qtd_avaliacoes': qtd_avaliacoes,
        'nota': nota,
        'categoria': categoria,
        'nota_pedestres': nota_pedestres,
        'restaurantes_perto': restaurantes_perto,
        'atracoes_perto': atracoes_perto,
        'latitude': lat,
        'longitude': lon,
        'fonte': entry_url,
    }
    print(nome + ' preco:' + preco)
    if not ONLY_REVIEWS:
        write_to_file(os.path.join(city_name,'hoteis.csv'), [data])
    return data 

#A partir de um link de restaurante, entra na pagina e extrai os seus dados
def get_restaurante_data(city_name, comentarios_flag, restaurantes_coletados, entry_link):
    entry_url = trip_url + entry_link
    soup = get_soup(entry_url)

    try:
        cidade = soup.find('a', id='global-nav-tourism').string
    except:
        cidade = 'indef'
    #if not cidade.replace(' ','') == city_name.replace(' ', ''):
    #    return {}

    restaurant_id = entry_link.split('-')[2][1:]
    if restaurantes_coletados is not None and not UPDATE_REVIEWS:
        if int(restaurant_id) in restaurantes_coletados['restaurante_id'].values:
            print(restaurant_id + ' já foi coletado')
            return {}

    try:
        nome = "\"" + soup.find('h1', {'data-test-target':'top-info-header'}).string.replace(',', ' |') + "\""
    except:
        nome = 'indef'
    try:
        endereco = '\"' + soup.find('a', {'class' : '_15QfMZ2L', 'href': '#MAPVIEW'}).string.strip() + '\"'
    except:
        endereco = 'indef'
    try:
        avaliacoes = soup.find('a', class_='_10Iv7dOs').string.split()[0].replace('.','')
    except:
        avaliacoes = '0'
    try:
        nota = soup.find('span', class_='r2Cf69qf').text.strip().replace(',','.')
    except:
        nota = 'indef'
    try:
        # So precisa acessar json se for pra escrever o restaurante
        if not ONLY_REVIEWS:
            api_url = 'https://www.tripadvisor.com.br/data/1.0/mapsEnrichment/restaurant/{}'.format(restaurant_id)
            api_json = requests.get(api_url).json()
        else:
            api_json = {}
        coords = api_json['geoPoint']
        lat = str(coords['latitude'])
        lon = str(coords['longitude'])
    except:
        lat = 'indef'
        lon = 'indef'
    try:
        categoria_preco = soup.find('span', class_='_13OzAOXO _34GKdBMV').find(string = lambda s: '$' in s)
        if categoria_preco is None:
            categoria_preco = 'indef'
    except:
        categoria_preco = 'indef'

    try:
        faixa_preco = soup.find(string='FAIXA DE PREÇO').parent.next_sibling.text
    except:
        faixa_preco = 'indef'
    
    if avaliacoes != '0' and comentarios_flag == 's':
        if UPDATE_REVIEWS:
            comentarios = atualiza_reviews(city_name, nome, restaurant_id, 'restaurante-review', entry_link, get_restaurante_review_data, get_restaurante_review_cards)
        else:
            comentarios = coleta_reviews(nome, restaurant_id, 'restaurante-review', entry_link, get_restaurante_review_data, get_restaurante_review_cards)
        write_to_file(os.path.join(city_name,'avaliacoes-restaurantes.csv'), comentarios)
    data = {
        'restaurante_id': restaurant_id,
        'nome': nome,
        'endereco': endereco,
        'cidade': cidade,
        'nota': nota,
        'qtd_avaliacoes': avaliacoes,
        'categoria_preco': categoria_preco,
        'faixa_preco': faixa_preco,
        'latitude': lat,
        'longitude': lon,
        'fonte': entry_url,
    }
    print(nome + ' coletado')
    if not ONLY_REVIEWS:
        write_to_file(os.path.join(city_name,'restaurantes.csv'), [data])
    return data

#A partir de um link de atracao, entra na pagina e extrai seus dados
def get_atracao_data(city_name, comentarios_flag, atracoes_coletadas, entry_link):
    entry_url = trip_url + entry_link
    soup = get_soup(entry_url)
    
    try:
        cidade = soup.find('a', class_="_1T4t-FiN").string
    except:
        try:
            cidade = soup.find("a", id="global-nav-tourism").string
        except:
            cidade = 'indef'
    if not cidade.replace(' ','') == city_name.replace(' ', ''):
        return {}

    atracao_id = entry_link.split('-')[2][1:]
    if atracoes_coletadas is not None and not UPDATE_REVIEWS:
        if int(atracao_id) in atracoes_coletadas['atracao_id'].values:
            return {}
    try:
        nome = "\"" + soup.find('h1', class_='DrjyGw-P _1SRa-qNz qf3QTY0F').string.strip().replace('\"','') + "\""
    except:
        try:
            nome = "\"" + soup.find("h1", id="HEADING").string.replace('\"','') + "\""
        except:
            nome = 'indef'
    try:
        endereco = '\"' + soup.find("button", class_="LgQbZEQC _1v-QphLm _1fKqJFvt").find('span', class_='DrjyGw-P _1l3JzGX1').string + '\"'
    except:
        endereco = 'indef'
    try:
        avaliacoes = soup.find('a', href='#REVIEWS').string.split()[0].replace('.','')
    except:
        avaliacoes = '0'
    try:
        nota = soup.find('div', class_='DrjyGw-P _1SRa-qNz _3t0zrF_f _1QGef_ZJ').string
    except:
        try:
            nota = soup.find("span", class_="ui_bubble_rating")['class'][1].split("_")[1]
            nota = nota[0] + "." + nota[1]
        except:
            nota = 'indef'
    try:
        # So precisa acessar json se for pra escrever a atracao
        if not ONLY_REVIEWS:
            api_url = 'https://www.tripadvisor.com.br/data/1.0/mapsEnrichment/attraction/{}'.format(atracao_id)
            api_json = requests.get(api_url).json()
        else:
            api_json = {}
        coords = api_json['geoPoint']
        lat = str(coords['latitude'])
        lon = str(coords['longitude'])
    except:
        lat = 'indef'
        lon = 'indef'
    
    if avaliacoes != '0' and comentarios_flag == 's':
        if UPDATE_REVIEWS:
            comentarios = atualiza_reviews(city_name, nome, atracao_id, 'atracao-review', entry_link, get_atracao_review_data, get_atracao_review_cards)
        else:
            comentarios = coleta_reviews(nome, atracao_id, 'atracao-review', lat, lon, entry_link, get_atracao_review_data, get_atracao_review_cards)
        write_to_file(os.path.join(city_name,'avaliacoes-atracoes.csv'), comentarios)
    data = {
        'atracao_id': atracao_id,
        'nome': nome,
        'endereco': endereco,
        'cidade': cidade,
        'nota': nota,
        'qtd_avaliacoes': avaliacoes,
        'latitude': lat,
        'longitude': lon,
        'fonte': entry_url,
    }
    print(nome + ' coletado')
    if not ONLY_REVIEWS:
        write_to_file(os.path.join(city_name,'atracoes.csv'), [data])
    return data

def get_hotel_review_data(id_, nome, tipo, driver, review_selenium):
    review = BeautifulSoup(review_selenium.get_attribute('innerHTML'), 'lxml')
    try:
        usuario = review.find('a', class_='ui_header_link _1r_My98y')['href'].split('/')[-1]
    except:
        usuario = 'indef'
    try:    
        data_avaliacao = review.find('a', class_='ui_header_link _1r_My98y').next_sibling.split()[3:]
        data_avaliacao = ' '.join(data_avaliacao)
        data_avaliacao = parse_date(data_avaliacao)
    except:
        data_avaliacao = 'indef'
    try:
        data_estadia = ' '.join(review.find('span', class_='_355y0nZn').next_sibling.split())
        data_estadia = parse_date(data_estadia)
    except:
        data_estadia = 'indef'
    try:
        nota = review.find(class_='nf9vGX55').find('span', class_='ui_bubble_rating')['class'][1][-2:]
        nota = nota[0] + '.' + nota[1]
    except:
        nota = 'indef'
    try:
        titulo = '\"' + review.find(class_='glasR4aX').string.replace('\"','') + '\"'
    except:
        titulo = 'indef'
    try:
        read_more = review_selenium.find_element_by_xpath(".//span[@class='_3maEfNCR']")
        driver.execute_script("arguments[0].click();", read_more)
        conteudo = '\"' + review_selenium.find_element_by_xpath(".//q[@class='IRsGHoPm']").text.replace('\"','').strip() + '\"'
        #conteudo = '\"' + review.find('q', class_='IRsGHoPm').text.replace('\"', "") + '\"'
    except:
        conteudo = 'indef'
    try:
        tipo_viagem = ' '.join(review.find('span', class_='_2bVY3aT5').text.split()[3:])
    except:
        tipo_viagem = 'indef'
    try:
        origem = '\"' + review.find('span', class_='default _3J15flPT small').text + '\"'
    except:
        origem = 'indef'

    data = {
        'estabelecimento': nome,
        'estabelecimento_id': id_,
        'estabelecimento_tipo': tipo,
        'usuario': usuario,
        'data_avaliacao': data_avaliacao,
        'data_estadia': data_estadia,
        'nota': nota,
        'titulo': titulo,
        'conteudo': conteudo,
        'tipo_viagem': tipo_viagem,
        'origem': origem
    }
    print(data)
    return data

def get_restaurante_review_data(id_, nome, tipo, driver, review_selenium):
    review = BeautifulSoup(review_selenium.get_attribute('innerHTML'), 'lxml')
    try:
        usuario = review.find('div', class_='info_text pointer_cursor').div.text
    except:
        usuario = 'indef'
    try:
        origem = '\"' + review.find('div', class_='userLoc').text + '\"'
    except:
        if usuario != 'indef':
            usuario_url = 'https://www.tripadvisor.com.br/Profile/' + usuario
            usuario_soup = get_soup(usuario_url)
        else:
            usuario_soup = None
            
        try:
            origem = '\"' + usuario_soup.find('span', class_='_2VknwlEe _3J15flPT default').text + '\"'
        except:
            origem = 'indef'
    try:    
        data_avaliacao = review.find('span', class_='ratingDate')['title']
        data_avaliacao = parse_date(data_avaliacao)
    except:
        data_avaliacao= 'indef'
    try:
        data_visita = ' '.join(review.find('div', class_='prw_rup prw_reviews_stay_date_hsx').text.split()[3:])
        data_visita = parse_date(data_visita)
    except:
        data_visita = 'indef'
    try:
        nota = review.find('span', class_='ui_bubble_rating')['class'][1][-2:]
        nota = nota[0] + '.' + nota[1]
    except:
        nota = 'indef'
    try:
        titulo = '\"'+ review.find('span', class_='noQuotes').text.replace('\"','') + '\"'
    except:
        titulo = 'indef'
    try:
        conteudo = '\"' + review_selenium.find_element_by_xpath(".//p[@class='partial_entry']").text.replace('\"','').strip() + '\"'

        #conteudo = '\"' + review.find('p', class_='partial_entry').text.replace('\"', '') + '\"'
    except:
        conteudo = 'indef'
    data = {
        'estabelecimento': nome,
        'estabelecimento_id': id_,
        'estabelecimento_tipo': tipo,
        'usuario': usuario,
        'data_avaliacao': data_avaliacao,
        'data_visita': data_visita,
        'nota': nota,
        'titulo': titulo,
        'conteudo': conteudo,
        'origem': origem
    }
    print(data)
    return data

def get_atracao_review_data(id_, nome, tipo, latitude, longitude, driver, review_selenium):
    review = BeautifulSoup(review_selenium.get_attribute('innerHTML'), 'lxml')
    try:
        usuario = review.find('a', class_='_7c6GgQ6n _37QDe3gr WullykOU _3WoyIIcL')['href'].split('/')[-1]
    except:
        usuario = 'indef'
    try:
        data_avaliacao = ' '.join(review.find('div', class_='DrjyGw-P _26S7gyB4 _1z-B2F-n _1dimhEoy').string.split()[2:])
        data_avaliacao = parse_date(data_avaliacao)
    except:
        data_avaliacao = 'indef'
    '''try:
        data_visita = review.find('div', class_='_3JxPDYSx').string.split("•")[0]
        data_visita = parse_date(data_visita)
    except:
        data_visita = 'indef'''
    try:
        nota = review.find('svg', class_='zWXXYhVR')['title'].split()[0].replace(",", ".")
    except:
        nota = 'indef'
    try:
        titulo = '\"' + review.find("span", class_='_2tsgCuqy').string.replace('\"','') + '\"'
    except:
        titulo = 'indef'
    try:
        read_more = review_selenium.find_element_by_xpath(".//button[@class='LgQbZEQC _1v-QphLm']")
        driver.execute_script("arguments[0].click();", read_more)
        div = review_selenium.find_element_by_xpath(".//div[@class='DrjyGw-P _26S7gyB4 _2nPM5Opx']")
        conteudo = '\"' + div.find_element_by_xpath(".//span[@class='_2tsgCuqy']").text.replace('\"','').strip() + '\"'
        
        #conteudo = '\"' + review.find('q', class_='IRsGHoPm').text.replace('\"','') + '\"'
    except:
        conteudo = 'indef'
    try:
        origem = '\"' + review.find('div', class_='DrjyGw-P _26S7gyB4 NGv7A1lw _2yS548m8 _2cnjB3re _1TAWSgm1 _1Z1zA2gh _2-K8UW3T _1dimhEoy').find("span").text + '\"'
    except:
        origem = 'indef'

    data = {
        'estabelecimento': nome,
        'estabelecimento_id': id_,
        'estabelecimento_tipo': tipo,
        'usuario': usuario,
        'data_avaliacao': data_avaliacao,
        #'data_visita': data_visita,
        'nota': nota,
        'titulo': titulo,
        'conteudo': conteudo,
        'origem': origem,
        'latitude': latitude,
        'longitude': longitude
    }
    return data

def get_hotel_review_cards(entry_url):
    #soup = get_soup(entry_url)
    #review_cards = soup.findAll('div', class_='_2wrUUKlw _3hFEdNs8')
    driver = get_driver_selenium(entry_url)
    review_cards = driver.find_elements_by_xpath("//div[@class='_2wrUUKlw _3hFEdNs8']")
    return review_cards, driver

def get_restaurante_review_cards(entry_url):
    #soup = get_soup(entry_url)
    #review_cards = soup.findAll('div', class_='review-container')
    driver = get_driver_selenium(entry_url)
    driver.implicitly_wait(5)
    review_cards = driver.find_elements_by_xpath("//div[@class='review-container']")
    
    # Ao clicar em um "ler mais", todos os outros comentarios da pagina se expandem
    try:
        read_more = driver.find_element_by_xpath(".//span[@class='taLnk ulBlueLinks']")
        driver.execute_script("arguments[0].click();", read_more)
    except:
        pass
    return review_cards, driver

def get_atracao_review_cards(entry_url):
    driver = get_driver_selenium(entry_url)
    review_cards = driver.find_elements_by_xpath("//div[@class='_1c8_1ITO']/*")[:-1]
    #soup = get_soup(entry_url)
    #review_cards = soup.findAll('div', class_='Dq9MAugU T870kzTX LnVzGwUB')
    return review_cards, driver

def coleta_review_por_url(get_review_data, get_review_cards, review_url):
    review_cards, driver = get_review_cards(review_url)
    if driver is not None:
        get_review_data = partial(get_review_data, driver)

    data = []
    for card in review_cards:
        d = get_review_data(card)
        data.append(d)
    
    if driver is not None:
        time.sleep(3)
        driver.quit()
    return data

def coleta_reviews(nome, id_, tipo_review, entry_link, lat, lon, get_review_data, get_review_cards):
    review_urls = get_reviews_page_urls(entry_link, tipo_review)
    collected_reviews = []
    for review_urls_by_language in review_urls:
        # Muitas paginas -> vale a pena filtrar
        if len(review_urls_by_language) >= TOO_MUCH_REVIEW_PAGES:
            review_urls_by_language = filter_old_reviews(review_urls_by_language, tipo_review)

        partial_extractor = partial(get_review_data, id_, nome, tipo_review, lat, lon)
        data_extractor = partial(coleta_review_por_url, partial_extractor, get_review_cards)
        
        with ThreadPoolExecutor(NUM_THREADS_FOR_REVIEW) as pool:
            d = pool.map(data_extractor, review_urls_by_language)
        data = reduce(lambda acc, x: acc + x, d)
        collected_reviews += data

    return collected_reviews

def atualiza_reviews(cidade, nome, id_, tipo_review, entry_link, get_review_data, get_review_cards):
    review_urls = get_reviews_page_urls(entry_link, tipo_review)
    last_scrape_date = get_last_scrape_date(cidade, tipo_review)
    partial_extractor = partial(get_review_data, id_, nome, tipo_review)

    collected_reviews = []
    for review_url_by_language in review_urls:
        done = False

        for url in review_url_by_language:
            review_cards, driver = get_review_cards(url)
            if driver is not None:
                data_extractor = partial(partial_extractor, driver)

            for card in review_cards:
                review = data_extractor(card)
                if review['data_avaliacao'] != 'indef':
                    review_date = int(review['data_avaliacao'].replace('-',''))
                    # Para de coletar se a data do review e mais antiga que a
                    # data da ultima coleta
                    if review_date > last_scrape_date:
                        collected_reviews.append(review)
                    else:
                        # Absolutamente terrivel esse jeito de sair dos loops
                        done = True
                        break

            if driver is not None:
                time.sleep(3)
                driver.quit()
            if done:
                break
    
    return collected_reviews

def get_last_scrape_date(cidade, tipo):
    if tipo == 'hotel-review':
        nome_arq = 'data_coleta_hotel.txt'
    elif tipo == 'restaurante-review':
        nome_arq = 'data_coleta_restaurante.txt'
    elif tipo == 'atracao-review':
        nome_arq = 'data_coleta_atracao.txt'
    
    with open(os.path.join(cidade, nome_arq), 'r') as f:
        data = f.read().strip().replace('-','')
        data = int(data)
    
    return data


#Infere o tipo a partir do nome do hotel
def get_type_by_name(name, possible_types):
    for tipo in possible_types:
        if tipo in name:
            return tipo
    if 'Chalé' in name or 'Chalés' in name or 'Chales' in name:
        return 'Chale'
    return "indef"

#Retorna os links dos hoteis presentes numa listagem
def get_hotel_links(url):
    driver = get_driver_selenium(url)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    time.sleep(3)
    driver.quit()
    listing_titles = soup.findAll(class_='listing_title')
    titles_links = []
    for entry in listing_titles:
        title_link = entry.find('a')['href']
        titles_links.append(title_link)

    return titles_links

#Retorna os links dos restaurantes presentes numa listagem
def get_restaurante_links(url):
    soup = get_soup(url)
    restaurant_items = soup.findAll(class_='_1llCuDZj')
    restaurant_links = []
    for restaurant in restaurant_items:
        restaurant_link = restaurant.find('a')['href']
        restaurant_links.append(restaurant_link)
    
    return restaurant_links

#Retorna os links das atracoes presentes numa listagem
def get_atracao_links(url):
    driver = get_driver_selenium(url)
    #Espera carregar
    driver.implicitly_wait(60)
    #WebDriverWait(driver, 60).until(
    #EC.presence_of_element_located((By.CLASS_NAME, "_1oY56Xsv")))

    atracoes_items = driver.find_elements_by_xpath("//div[@class='_3JZh_6Iu']")
    atracoes_links = []
    for atracao in atracoes_items:
        atracao_link = '/' + atracao.find_element_by_tag_name('a').get_attribute('href').split('/')[-1]
        atracoes_links.append(atracao_link)
    
    time.sleep(3)
    driver.quit()
    return atracoes_links

#Gera, a partir de uma URl inicial, as URLS correspondentes ao avançar uma pagina
def get_page_urls(initial_url, page_type):
    urls=[initial_url]
    try:
        num_pages = get_max_num_pages(initial_url, page_type)
    except:
        return urls

    if page_type in ['hotel', 'restaurante', 'atracao']:
        entries_by_page = 30
        offset_package = 'oa{}'
    elif page_type in ['hotel-review', 'restaurante-review', 'atracao-review']:
        offset_package = 'or{}'
        pos_to_insert = 4
    if page_type == 'hotel' or page_type == 'restaurante':
        pos_to_insert = 2
    elif page_type == 'atracao':
        pos_to_insert = 3
    elif page_type == 'restaurante-review' or page_type == 'atracao-review':
        entries_by_page = 10
    elif page_type == 'hotel-review':
        entries_by_page = 5

    data_offset = entries_by_page
    url_to_offset = initial_url.split('-')
    url_to_offset.insert(pos_to_insert, offset_package)
    url_to_offset = '-'.join(url_to_offset)

    for _ in range(1,num_pages):
        url = url_to_offset.format(data_offset)
        urls.append(url)
        data_offset= data_offset + entries_by_page

    return urls

def get_reviews_page_urls(entry_link, page_type):
    urls = []
    for LANGUAGE in LANGUAGES_TO_COLLECT:
        full_url = 'https://www.tripadvisor.com' + LANGUAGE + entry_link
        urls_by_language = get_page_urls(full_url, page_type)
        urls.append(urls_by_language)
    return urls

#Escreve os dados coletados em um arquivo .csv
def write_to_file(filename, data):
    with open(filename, "a") as f:
        if os.stat(filename).st_size == 0:
            header_buffer = ','.join(data[0].keys()) + '\n'
            f.write(header_buffer)
        for instance in data:
            values = instance.values()
            if len(values) != 0:
                buffer = ",".join(values)
                f.write(buffer+"\n")

#Retorna o numero de paginas total
def get_max_num_pages(url, page_type):
    soup = get_soup(url)
    if 'restaurante-review' in page_type:
        num_pages = soup.find('div', id='REVIEWS').findAll('a', class_="pageNum")[-1].string
    elif "atracao" in page_type:
        num_pages = soup.findAll("div", class_="_1w5PB8Rk")[-1].string
    elif "hotel" == page_type:
        total_entries = int(soup.find("span", class_="_3nOjB60a").string.split()[0].replace(".",""))
        num_pages = math.ceil(total_entries/30)
    else:
        num_pages = soup.findAll('a', class_="pageNum")[-1].string
    return int(num_pages)

#Coleta dados de hoteis/restaurantes/atracoes (lista de listas)
def coleta_dados(cidade, initial_url, data_extractor, get_links, page_type, comentarios_flag, instancias_coletadas):
    page_urls = get_page_urls(initial_url, page_type)
    data_extractor = partial(data_extractor, cidade, comentarios_flag, instancias_coletadas)
    data = []
    for url in page_urls:
        links = get_links(url)
        with ThreadPoolExecutor(NUM_THREADS_FOR_PLACE) as pool:
            d = pool.map(data_extractor, links)
        data += list(d)

    return data

def coleta_hoteis(cidade, url, comentarios_flag):
    filename = os.path.join(cidade,'hoteis.csv')
    try:
        hoteis_coletados = pd.read_csv(filename)
    except:
        hoteis_coletados = None

    hoteis = coleta_dados(cidade, url, get_hotel_data, get_hotel_links, 'hotel', comentarios_flag, hoteis_coletados)
    print("\n{} hoteis coletados\n".format(len(hoteis)))

def coleta_restaurantes(cidade, url, comentarios_flag):
    filename = os.path.join(cidade,'restaurantes.csv')
    try:
        restaurantes_coletados = pd.read_csv(filename)
    except:
        restaurantes_coletados = None
    
    restaurantes = coleta_dados(cidade, url, get_restaurante_data, get_restaurante_links, 'restaurante', comentarios_flag, restaurantes_coletados)
    print('\n{} restaurantes coletados\n'.format(len(restaurantes)))

def coleta_atracoes(cidade, url, comentarios_flag):
    filename = os.path.join(cidade,'atracoes.csv')
    try:
        atracoes_coletadas = pd.read_csv(filename)
    except:
        atracoes_coletadas = None

    atracoes = coleta_dados(cidade, url, get_atracao_data, get_atracao_links, 'atracao', comentarios_flag, atracoes_coletadas)
    print('\n{} atracoes coletadas\n'.format(len(atracoes)))

def get_links_from_city(city_url):
    soup = get_soup(city_url)
    links = soup.findAll('a', {'class': '_1ulyogkG'})
    hotel_url = 'https://www.tripadvisor.com.br'+ links[0]['href']
    restaurante_url = 'https://www.tripadvisor.com.br' + links[3]['href']
    atracao_url = 'https://www.tripadvisor.com.br' + links[2]['href']
    atracao_url = atracao_url.split('-')
    atracao_url.insert(3, 'a_allAttractions.true')
    atracao_url = '-'.join(atracao_url)
    
    return (hotel_url, restaurante_url, atracao_url)

def coleta_por_cidade(city_name, city_url, mode):
    hotel_url, restaurante_url, atracao_url = get_links_from_city(city_url)
    if '1' in mode:
        coleta_hoteis(city_name, hotel_url, mode[-1])
        marca_data_coleta(city_name, 'hotel')
    if '2' in mode:
        coleta_restaurantes(city_name, restaurante_url, mode[-1])
        marca_data_coleta(city_name, 'restaurante')
    if '3' in mode:
        coleta_atracoes(city_name, atracao_url, mode[-1])
        marca_data_coleta(city_name, 'atracao')

def coleta_cidades(cidades, mode):
    for nome_cidade, url in cidades.items():
        coleta_por_cidade(nome_cidade, url, mode)

def clear_files(nome_cidades, mode):
    for cidade in nome_cidades:
        if '1' in mode:
            if not ONLY_REVIEWS:
                open(os.path.join(cidade,'hoteis.csv'), 'w').close()
            if 's' in mode and not UPDATE_REVIEWS:
                open(os.path.join(cidade,'avaliacoes-hoteis.csv'), 'w').close()
        if '2' in mode:
            if not ONLY_REVIEWS:
                open(os.path.join(cidade,'restaurantes.csv'), 'w').close()
            if 's' in mode and not UPDATE_REVIEWS:
                open(os.path.join(cidade,'avaliacoes-restaurantes.csv'), 'w').close()
        if '3' in mode:
            if not ONLY_REVIEWS:
                open(os.path.join(cidade,'atracoes.csv'), 'w').close()
            if 's' in mode and not UPDATE_REVIEWS:
                open(os.path.join(cidade,'avaliacoes-atracoes.csv'), 'w').close()

def extrai_datas(review_cards, tipo):
    datas = []

    if tipo == 'hotel-review':
        for card in review_cards:
            try:
                data_avaliacao = card.find('a', class_='ui_header_link _1r_My98y').next_sibling.split()[3:]
                data_avaliacao = ' '.join(data_avaliacao)
                data_avaliacao = parse_date(data_avaliacao)
            except:
                data_avaliacao = 'indef'
            datas.append(data_avaliacao)

    elif tipo == 'restaurante-review':
        for card in review_cards:
            try:
                data_avaliacao = card.find('span', class_='ratingDate')['title']
                data_avaliacao = parse_date(data_avaliacao)
            except:
                data_avaliacao = 'indef'
            datas.append(data_avaliacao)
    
    elif tipo == 'atracao-review':
        for card in review_cards:
            try:
                data_avaliacao = ' '.join(card.find('div', class_='DrjyGw-P _26S7gyB4 _1z-B2F-n _1dimhEoy').string.split()[2:])
                data_avaliacao = parse_date(data_avaliacao)
            except:
                data_avaliacao = 'indef'
            datas.append(data_avaliacao)

    return datas

# Retorno a indice em review_urls que contem o ultimo comentario de year
def binary_search(review_urls, tipo, low, high, index): 
  
    if high >= low: 
        
        # Carrega os reviews da pagina no meio do vetor
        mid = (high + low) // 2
        mid_url = review_urls[mid]
        soup = get_soup(mid_url)
        
        # Extrai as datas dos reviews da pagina
        if tipo == 'atracao-review':
            big_div = soup.find('div', class_='_1c8_1ITO')
            review_cards = big_div.findAll("div", recursive=False)[:-1]

        elif tipo == 'hotel-review':
            review_cards = soup.findAll('div', class_='_2wrUUKlw _3hFEdNs8')

        elif tipo == 'restaurante-review':
            review_cards = soup.findAll('div', class_='review-container')
        
        page_review_dates = extrai_datas(review_cards, tipo)

        # Pega o primeiro ano valido
        for date in page_review_dates:
            if date != 'indef':
                review_year = int(date.split('-')[0])
                break

        # Se a ano do primeiro review da pagina eh maior que o ano limite, tenho
        # que percorrer pelo menos ate "mid" e continua indo para a direita
        if review_year >= COLLECT_UNTIL: 
            return binary_search(review_urls, tipo, mid + 1, high, mid) 
  
        # Caso contrario, eu "passei do ponto" e tenho que ir para a esquerda
        else:           
            return binary_search(review_urls, tipo, low, mid - 1, index)  
  
    else: 
        return index

# Filtra as paginas que contem reviews muito antigos
def filter_old_reviews(review_urls, tipo):
    try:
        index = binary_search(review_urls, tipo, 0, len(review_urls)-1, -1)
        return review_urls[:index+1]
    except:
        return review_urls

def make_dirs(nome_cidades):
    for nome in nome_cidades:
        if not os.path.exists(nome):
            os.mkdir(nome)

def marca_data_coleta(cidade, tipo):
    data = str(datetime.datetime.now()).split(' ')[0]
    if tipo == 'hotel':
        with open(os.path.join(cidade, 'data_coleta_hotel.txt'), 'w') as f:
            f.write(data+'\n')
    if tipo == 'atracao':
        with open(os.path.join(cidade, 'data_coleta_atracao.txt'), 'w') as f:
            f.write(data+'\n')
    if tipo == 'restaurante':
        with open(os.path.join(cidade, 'data_coleta_restaurante.txt'), 'w') as f:
            f.write(data+'\n')


if __name__ == "__main__":
    start_time = time.time()
    cidades = {
            'Ouro Preto': 'https://www.tripadvisor.com.br/Tourism-g303389-Ouro_Preto_State_of_Minas_Gerais-Vacations.html'
    }
    nome_cidades = cidades.keys()
    make_dirs(nome_cidades)

    tipo_coleta = input('Digite o modo de coleta (1: hoteis; 2: restaurantes; 3: atracoes)> ')
    comentarios_flag = input('Deseja coletar os comentarios? (s/n)> ')
    mode = tipo_coleta + comentarios_flag
    clear_flag = True if input('Deseja limpar os arquivos? (s/n)> ') == 's' else False
    
    if clear_flag is True:
        clear_files(nome_cidades, mode)
    
    coleta_cidades(cidades, mode)

    print('tempo de execução: {} minutos'.format((time.time() - start_time)/60))
