# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests
import json
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

#session = requests.Session()
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36'}
language = '.br'
trip_url = 'https://www.tripadvisor.com' + language
LANGUAGES_TO_COLLECT = ['.br', ''] # '' significa para coletar em ingles
REQUEST_DELAY = 10
COLLECT_UNTIL = 2015
ONLY_REVIEWS = False
UPDATE_REVIEWS = False

def get_soup(url):
    time.sleep(REQUEST_DELAY)
    r = requests.get(url, headers=headers)
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
    wd = webdriver.Chrome(options=chrome_options)
    wd.get(url)
    time.sleep(REQUEST_DELAY)
    return wd

#A partir de um link de hotel, entra na pagina do hotel em questao
#e extrai seus dados
def get_hotel_data(city_name, comentarios_flag, entry_link):
    entry_url = trip_url + entry_link
    driver = get_driver_selenium(entry_url)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    #soup = get_soup(entry_url)

    cidade = soup.find('a', id='global-nav-tourism').string
    if not cidade.replace(' ','') == city_name.replace(' ', ''):
        return {}

    try:
        nome = soup.find(id="HEADING").string.strip()
    except:
        nome = 'indef'
    try:
        preco =  WebDriverWait(driver, 2*REQUEST_DELAY).until(
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

    hotel_id = entry_link.split("-")[2][1:]
    try:
        # So precisa acessar json se for pra escrever os hoteis
        if not ONLY_REVIEWS:
            api_url = 'https://www.tripadvisor.com.br/data/1.0/mapsEnrichment/hotel/{}?rn=1&rc=Hotel_Review&stayDates=2021_2_11_2021_2_12&guestInfo=1_2&placementName=Hotel_Review_MapDetail_Anchor&currency=BRL'.format(hotel_id)
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
    return data 

#A partir de um link de restaurante, entra na pagina e extrai os seus dados
def get_restaurante_data(city_name, comentarios_flag, entry_link):
    entry_url = trip_url + entry_link
    soup = get_soup(entry_url)

    cidade = soup.find('a', id='global-nav-tourism').string
    if not cidade.replace(' ','') == city_name.replace(' ', ''):
        return {}

    try:
        nome = soup.find('h1', {'data-test-target':'top-info-header'}).string.replace(',', ' |')
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
        restaurant_id = entry_link.split('-')[2][1:]
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
    return data

#A partir de um link de atracao, entra na pagina e extrai seus dados
def get_atracao_data(city_name, comentarios_flag, entry_link):
    entry_url = trip_url + entry_link
    soup = get_soup(entry_url)
    
    cidade = soup.find('a', id='global-nav-tourism').string
    if not cidade.replace(' ','') == city_name.replace(' ', ''):
        return {}

    try:
        nome = soup.find('h1', id='HEADING').string.strip().replace('\"','')
    except:
        nome = 'indef'
    try:
        endereco = '\"' + soup.find('div', class_='LjCWTZdN').findAll('span')[1].string + '\"'
    except:
        endereco = 'indef'
    try:
        avaliacoes = soup.find('span', class_='_3WF_jKL7 _1uXQPaAr').string.split()[0].replace('.','')
    except:
        avaliacoes = '0'
    try:
        nota = soup.find('span', class_='ui_bubble_rating')['class'][1][-2:]
        nota = nota[0] + '.' + nota[1]
    except:
        nota = 'indef'
    try:
        atracao_id = entry_link.split('-')[2][1:]
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
            comentarios = coleta_reviews(nome, atracao_id, 'atracao-review', entry_link, get_atracao_review_data, get_atracao_review_cards)
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
        # So precisa pegar origem se for para escrever os restaurantes coletados
        if not ONLY_REVIEWS:
            usuario_url = 'https://www.tripadvisor.com.br/Profile/' + usuario
            usuario_soup = get_soup(usuario_url)
        else:
            usuario_soup = None
        try:
            origem = '\"' + usuario_soup.find('span', class_='_2VknwlEe _3J15flPT default').text + '\"'
        except:
            try:
                origem = '\"' + review.find('div', class_='userLoc').text + '\"'
            except:
                origem = 'indef'
    except:
        usuario = 'indef'
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

def get_atracao_review_data(id_, nome, tipo, driver, review_selenium):
    review = BeautifulSoup(review_selenium.get_attribute('innerHTML'), 'lxml')
    try:
        usuario = review.find('a', class_='_3x5_awTA ui_social_avatar inline')['href'].split('/')[-1]
    except:
        usuario = 'indef'
    try:
        data_avaliacao = review.find('a', class_='ui_header_link _1r_My98y').next_sibling.split()[3:]
        data_avaliacao = ' '.join(data_avaliacao)
        data_avaliacao = parse_date(data_avaliacao)
    except:
        data_avaliacao = 'indef'
    try:
        data_visita = ' '.join(review.find('span', class_='_355y0nZn').next_sibling.split())
        data_visita = parse_date(data_visita)
    except:
        data_visita = 'indef'
    try:
        nota = review.find('span', class_='ui_bubble_rating')['class'][1][-2:]
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
        
        #conteudo = '\"' + review.find('q', class_='IRsGHoPm').text.replace('\"','') + '\"'
    except:
        conteudo = 'indef'
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
        'data_visita': data_visita,
        'nota': nota,
        'titulo': titulo,
        'conteudo': conteudo,
        'origem': origem
    }
    print(data)
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
    review_cards = driver.find_elements_by_xpath("//div[@class='review-container']")
    
    # Ao clicar em um "ler mais", todos os outros comentarios da pagina se expandem
    try:
        read_more = driver.find_element_by_xpath(".//span[@class='taLnk ulBlueLinks']")
        driver.execute_script("arguments[0].click();", read_more)
        time.sleep(2)
    except:
        pass
    return review_cards, driver

def get_atracao_review_cards(entry_url):
    driver = get_driver_selenium(entry_url)
    review_cards = driver.find_elements_by_xpath("//div[@class='Dq9MAugU T870kzTX LnVzGwUB']")
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

def coleta_reviews(nome, id_, tipo_review, entry_link, get_review_data, get_review_cards):
    review_urls = get_reviews_page_urls(entry_link, tipo_review)
    collected_reviews = []
    for review_urls_by_language in review_urls:
        # Muitas paginas -> vale a pena filtrar
        if len(review_urls_by_language) > 100:
            review_urls_by_language = filter_old_reviews(review_urls_by_language, tipo_review)

        partial_extractor = partial(get_review_data, id_, nome, tipo_review)
        data_extractor = partial(coleta_review_por_url, partial_extractor, get_review_cards)
        
        with ThreadPoolExecutor(10) as pool:
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
    soup = get_soup(url)
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

    atracoes_items = driver.find_elements_by_xpath("//div[@class='_1oY56Xsv']")
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
    except IndexError:
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
    elif page_type == 'restaurante-review':
        entries_by_page = 10
    elif page_type == 'hotel-review' or page_type == 'atracao-review':
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
    elif 'atracao' == page_type:
        driver = get_driver_selenium(url)
        driver.implicitly_wait(60)
        last_page_button = driver.find_elements_by_xpath("//a[@class='_3ghuVozE _2xHyLFC5 _27ZzJr-O']")[-1]
        num_pages = last_page_button.get_attribute('aria-label')
        time.sleep(3)
        driver.quit()
    else:
        num_pages = soup.findAll('a', class_="pageNum")[-1].string
    return int(num_pages)

#Coleta dados de hoteis/restaurantes/atracoes (lista de listas)
def coleta_dados(cidade, initial_url, data_extractor, get_links, page_type, comentarios_flag):
    page_urls = get_page_urls(initial_url, page_type)
    data_extractor = partial(data_extractor, cidade, comentarios_flag)
    data = []
    for url in page_urls:
        links = get_links(url)
        with ThreadPoolExecutor(1) as pool:
            d = pool.map(data_extractor, links)
        data += list(d)

    return data

def coleta_hoteis(cidade, url, comentarios_flag):
    hoteis = coleta_dados(cidade, url, get_hotel_data, get_hotel_links, 'hotel', comentarios_flag)
    if not ONLY_REVIEWS:
        write_to_file(os.path.join(cidade,'hoteis.csv'), hoteis)
    print(f"\n{len(hoteis)} hoteis coletados\n")

def coleta_restaurantes(cidade, url, comentarios_flag):
    restaurantes = coleta_dados(cidade, url, get_restaurante_data, get_restaurante_links, 'restaurante', comentarios_flag)
    if not ONLY_REVIEWS:
        write_to_file(os.path.join(cidade,'restaurantes.csv'), restaurantes)
    print(f'\n{len(restaurantes)} restaurantes coletados\n')

def coleta_atracoes(cidade, url, comentarios_flag):
    atracoes = coleta_dados(cidade, url, get_atracao_data, get_atracao_links, 'atracao', comentarios_flag)
    if not ONLY_REVIEWS:
        write_to_file(os.path.join(cidade, 'atracoes.csv'), atracoes)
    print(f'\n{len(atracoes)} atracoes coletadas\n')

def get_links_from_city(city_url):
    soup = get_soup(city_url)
    hotel_url = 'https://www.tripadvisor.com.br'+ soup.find('a', {'class': '_1yB-kafB', 'title':'Hotéis'})['href']
    restaurante_url = 'https://www.tripadvisor.com.br' + soup.find('a', {'class': '_1yB-kafB', 'title':'Restaurantes'})['href']
    atracao_url = 'https://www.tripadvisor.com.br' + soup.find('a', {'class': '_1yB-kafB', 'title':'O que fazer'})['href']
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

# Retorno a indice em review_urls que contem o ultimo comentario de year
def binary_search(review_urls, tipo, low, high, index): 
  
    if high >= low: 
        
        # Carrega os reviews da pagina no meio do vetor
        mid = (high + low) // 2
        
        if tipo == 'atracao-review':
            extractor = partial(get_atracao_review_data,'','','')
            reviews = coleta_review_por_url(extractor, get_atracao_review_cards, review_urls[mid])
        elif tipo == 'hotel-review':
            extractor = partial(get_hotel_review_data,'','','')
            reviews = coleta_review_por_url(extractor, get_hotel_review_cards, review_urls[mid])
        else:
            extractor = partial(get_restaurante_review_data,'','','')
            reviews = coleta_review_por_url(extractor, get_restaurante_review_cards, review_urls[mid])

        for review in reviews:
            if review['data_avaliacao'] != 'indef':
                review_year = int(review['data_avaliacao'].split('-')[0])
                break
        

        # Se a ano do review da pagina eh maior que o ano limite, tenho
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
    index = binary_search(review_urls, tipo, 0, len(review_urls)-1, -1)
    return review_urls[:index+1]

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

    print(f'tempo de execução: {(time.time() - start_time)/60} minutos')
