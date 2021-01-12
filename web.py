from bs4 import BeautifulSoup
import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial, reduce


def get_soup(url):
    time.sleep(1)
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    return soup

#A partir de um link de hotel, entra na pagina do hotel em questão
#e extrai seus dados
def get_hotel_data(entry_link):
    entry_url = 'https://www.tripadvisor.com.br' + entry_link
    soup = get_soup(entry_url)
    nome = soup.find(id="HEADING").string.strip()
    cidade = soup.find('a', id='global-nav-tourism').string

    try:
        endereco = soup.find(class_='_3ErVArsu jke2_wbp').string.replace(","," |")
    except:
        endereco = "indef"
    try:
        qtd_avaliacoes = soup.find("span", class_='_33O9dg0j').string.split()[0]
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
        api_url = 'https://www.tripadvisor.com.br/data/1.0/mapsEnrichment/hotel/{}?rn=1&rc=Hotel_Review&stayDates=2021_2_11_2021_2_12&guestInfo=1_2&placementName=Hotel_Review_MapDetail_Anchor&currency=BRL'.format(hotel_id)
        api_json = requests.get(api_url).json()
        coords = api_json['hotels'][0]['location']['geoPoint']
        lat = str(coords['latitude'])
        lon = str(coords['longitude'])
    except:
        lat = "indef"
        lon = "indef"

    #comentarios = coleta_reviews(hotel_id, nome, 'hotel', 'hotel-review', entry_url, get_hotel_review_data, get_hotel_review_cards)
    data ={
        'hotel_id': hotel_id,
        'nome': nome,
        'endereco': endereco,
        'cidade': cidade,
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
        'fonte': entry_url
    }
    print(data)
    return data 

#A partir de um link de restaurante, entra na pagina e extrai os seus dados
def get_restaurante_data(entry_link):
    entry_url = 'https://www.tripadvisor.com.br' + entry_link
    soup = get_soup(entry_url)
    try:
        nome = soup.find('h1', {'data-test-target':'top-info-header'}).string.replace(',', ' |')
    except:
        nome = 'indef'
    cidade = soup.find('a', id='global-nav-tourism').string

    try:
        endereco = soup.find('a', {'class' : '_15QfMZ2L', 'href': '#MAPVIEW'}).string.strip().replace(',',' |')
    except:
        endereco = 'indef'
    try:
        avaliacoes = soup.find('a', class_='_10Iv7dOs').string.split()[0]
    except:
        avaliacoes = 'indef'
    try:
        nota = soup.find('span', class_='r2Cf69qf').text.strip().replace(',','.')
    except:
        nota = 'indef'
    try:
        restaurant_id = entry_link.split('-')[2][1:]
        api_url = 'https://www.tripadvisor.com.br/data/1.0/mapsEnrichment/restaurant/{}'.format(restaurant_id)
        api_json = requests.get(api_url).json()
        coords = api_json['geoPoint']
        lat = str(coords['latitude'])
        lon = str(coords['longitude'])
    except:
        lat = 'indef'
        lon = 'indef'
    
    data = {
        'restaurante_id': restaurant_id,
        'nome': nome,
        'endereco': endereco,
        'cidade': cidade,
        'nota': nota,
        'qtd_avaliacoes': avaliacoes,
        'latitude': lat,
        'longitude': lon,
        'fonte': entry_url
    }
    print(data)
    return data

#A partir de um link de atracao, entra na pagina e extrai seus dados
def get_atracao_data(entry_link):
    entry_url = 'https://www.tripadvisor.com.br' + entry_link
    soup = get_soup(entry_url)
    try:
        nome = soup.find('h1', id='HEADING').string.strip()
    except:
        nome = 'indef'
    cidade = soup.find('a', id='global-nav-tourism').string

    try:
        endereco = soup.find('div', class_='LjCWTZdN').findAll('span')[1].string.replace(',', ' |')
    except:
        endereco = 'indef'
    try:
        avaliacoes = soup.find('span', class_='_3WF_jKL7 _1uXQPaAr').string.split()[0]
    except:
        avaliacoes = '0'
    try:
        nota = soup.find('span', class_='ui_bubble_rating')['class'][1][-2:]
        nota = nota[0] + '.' + nota[1]
    except:
        nota = 'indef'
    try:
        atracao_id = entry_link.split('-')[2][1:]
        api_url = 'https://www.tripadvisor.com.br/data/1.0/mapsEnrichment/attraction/{}'.format(atracao_id)
        api_json = requests.get(api_url).json()
        coords = api_json['geoPoint']
        lat = str(coords['latitude'])
        lon = str(coords['longitude'])
    except:
        lat = 'indef'
        lon = 'indef'
    
    data = {
        'atracao_id': atracao_id,
        'nome': nome,
        'endereco': endereco,
        'cidade': cidade,
        'nota': nota,
        'qtd_avaliacoes': avaliacoes,
        'latitude': lat,
        'longitude': lon,
        'fonte': entry_url
    }
    print(data)
    return data

def get_hotel_review_data(id_, nome, tipo, review):
    usuario = review.find('a', class_='ui_header_link _1r_My98y')['href'].split('/')[-1]
    data_avaliacao = review.find('a', class_='ui_header_link _1r_My98y').parent.text.split()
    data_avaliacao = ' '.join(data_avaliacao[data_avaliacao.index('avaliação')+1:])
    data_estadia = ' '.join(review.find('span', class_='_34Xs-BQm').text.split()[-3:])
    nota = review.find(class_='nf9vGX55').find('span', class_='ui_bubble_rating')['class'][1][-2:]
    nota = nota[0] + '.' + nota[1]
    titulo = '\"' + review.find(class_='glasR4aX').string + '\"'
    conteudo = '\"' + review.find('q', class_='IRsGHoPm').text + '\"'
    try:
        tipo_viagem = ' '.join(review.find('span', class_='_2bVY3aT5').text.split()[3:])
    except:
        tipo_viagem = 'indef'
    try:
        origem = review.find('span', class_='default _3J15flPT small').text
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

def get_restaurante_review_data(id_, nome, tipo, review):
    usuario = review.find('div', class_='info_text pointer_cursor').text
    data_avaliacao = review.find('span', class_='ratingDate')['title']
    data_visita = ' '.join(review.find('div', class_='prw_rup prw_reviews_stay_date_hsx').text.split()[3:])
    nota = review.find('span', class_='ui_bubble_rating')['class'][1][-2:]
    nota = nota[0] + '.' + nota[1]
    titulo = '\"'+ review.find('span', class_='noQuotes').text + '\"'
    conteudo = '\"' + review.find('p', class_='partial_entry').text + '\"'
    #origem = review.find(class_='userLoc')
    data = {
        'estabelecimento': nome,
        'estabelecimento_id': id_,
        'estabelecimento_tipo': tipo,
        'usuario': usuario,
        'data_avaliacao': data_avaliacao,
        'data_visita': data_visita,
        'nota': nota,
        'titulo': titulo,
        'conteudo': conteudo
    }
    
    print(data)
    return data

def get_atracao_review_data(id_, nome, tipo, review):
    usuario = review.find('a', class_='_3x5_awTA ui_social_avatar inline')['href'].split('/')[-1]
    try:
        data_avaliacao = review.find('a', class_='ui_header_link _1r_My98y').parent.text.split()
        data_avaliacao = ' '.join(data_avaliacao[data_avaliacao.index('avaliação')+1:])
    except:
        data_avaliacao = 'indef'
    try:
        data_visita = ' '.join(review.find('span', class_='_34Xs-BQm').text.split()[3:])
    except:
        data_visita = 'indef'
    nota = review.find('span', class_='ui_bubble_rating')['class'][1][-2:]
    nota = nota[0] + '.' + nota[1]
    titulo = '\"' + review.find(class_='glasR4aX').string + '\"'
    conteudo = '\"' + review.find('q', class_='IRsGHoPm').text + '\"'
    try:
        origem = review.find('span', class_='default _3J15flPT small').text
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
    soup = get_soup(entry_url)
    review_cards = soup.findAll('div', class_='_2wrUUKlw _3hFEdNs8')
    return review_cards

def get_restaurante_review_cards(entry_url):
    soup = get_soup(entry_url)
    review_cards = soup.findAll('div', class_='review-container')
    return review_cards

def get_atracao_review_cards(entry_url):
    soup = get_soup(entry_url)
    review_cards = soup.findAll('div', class_='Dq9MAugU T870kzTX LnVzGwUB')
    return review_cards

def coleta_review_por_url(get_review_data, get_review_cards, review_url):
    review_cards = get_review_cards(review_url)
    data = map(get_review_data, review_cards)
    return list(data)

def coleta_reviews(nome, id_, tipo, tipo_review, entry_url, get_review_data, get_review_cards):
    review_urls = get_page_urls(entry_url, tipo_review)
    get_review_data = partial(get_review_data, id_, nome, tipo)
    data_extractor = partial(coleta_review_por_url, get_review_data, get_review_cards)
    with ThreadPoolExecutor() as pool:
        d = pool.map(data_extractor, review_urls)
    data = reduce(lambda acc, x: acc + x, d)
   
    '''for review_url in review_urls:
        review_cards = get_review_cards(review_url)
        with ThreadPoolExecutor() as pool:
            d = pool.map(get_review_data, review_cards)
        data += list(d)'''
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
    soup = get_soup(url)
    atracoes_items = soup.findAll('a', class_='_1QKQOve4')
    atracoes_links = []
    for atracao in atracoes_items:
        atracao_link = atracao['href']
        atracoes_links.append(atracao_link)
    
    return atracoes_links

#Gera, a partir de uma URl inicial, as URLS correspondentes ao avançar uma página
def get_page_urls(initial_url, page_type):
    urls=[initial_url]
    num_pages = get_max_num_pages(initial_url)

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

#Escreve os dados coletados em um arquivo .csv
def write_to_file(filename, data):
    with open(filename, "a") as f:
        for instance in data:
            values = instance.values()
            buffer = ",".join(values)
            f.write(buffer+"\n")

#Retorna o numero de paginas total
def get_max_num_pages(url):
    soup = get_soup(url)
    num_pages = soup.findAll('a', class_="pageNum")[-1].string
    return int(num_pages)

#Coleta dados de hoteis/restaurantes/atracoes (lista de listas)
def coleta_dados(initial_url, data_extractor, get_links, page_type):
    page_urls = get_page_urls(initial_url, page_type)

    data = []
    for url in page_urls:
        links = get_links(url)
        with ThreadPoolExecutor() as pool:
            d = pool.map(data_extractor, links)
        data += list(d)

    return data

def coleta_hoteis(url):
    hoteis = coleta_dados(url, get_hotel_data, get_hotel_links, 'hotel')
    write_to_file('hoteis.csv', hoteis)
    print(f'\n{len(hoteis)} hoteis coletados\n')

def coleta_restaurantes(url):
    restaurantes = coleta_dados(url, get_restaurante_data, get_restaurante_links, 'restaurante')
    write_to_file('restaurantes.csv', restaurantes)
    print(f'\n{len(restaurantes)} restaurantes coletados\n')

def coleta_atracoes(url):
    atracoes = coleta_dados(url, get_atracao_data, get_atracao_links, 'atracao')
    write_to_file('atracoes.csv', atracoes)
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

def coleta_por_cidade(city_url):
    hotel_url, restaurante_url, atracao_url = get_links_from_city(city_url)
    coleta_hoteis(hotel_url)
    coleta_restaurantes(restaurante_url)
    coleta_atracoes(atracao_url)

def coleta_cidades(city_url_list):
    create_files()
    for city_url in city_url_list:
        coleta_por_cidade(city_url)

def create_files():
    hotel_header = ['hotel_id', 'nome', 'endereco', 'cidade', 'tipo', 'qtd_quartos',
    'qtd_avaliacoes', 'nota', 'categoria', 'nota_pedestres',
    'restaurantes_perto', 'atracoes_perto', 'latitude', 'longitude',
    'fonte']
    restaurante_header = ['restaurante_id', 'nome', 'endereco', 'cidade', 'nota', 'qtd_avaliacoes',
    'latitude', 'longitude', 'fonte']
    atracao_header = ['atracao_id', 'nome', 'endereco', 'cidade', 'nota', 'qtd_avaliacoes',
    'latitude', 'longitude', 'fonte']

    with open('hoteis.csv','w') as f:
        header_buffer = ",".join(hotel_header) + "\n"
        f.write(header_buffer)
    with open('restaurantes.csv', 'w') as f:
        header_buffer = ",".join(restaurante_header) + "\n"
        f.write(header_buffer)
    with open('atracoes.csv', 'w') as f:
        header_buffer = ",".join(atracao_header) + "\n"
        f.write(header_buffer)

if __name__ == "__main__":
    '''
    start_time = time.time()
    cidades_url = ['https://www.tripadvisor.com.br/Tourism-g303389-Ouro_Preto_State_of_Minas_Gerais-Vacations.html', 
    'https://www.tripadvisor.com.br/Tourism-g303386-Mariana_State_of_Minas_Gerais-Vacations.html']
    coleta_cidades(cidades_url)
    print(f'tempo de execução: {(time.time() - start_time)/60} minutos')
    '''
    start_time = time.time()
    coleta_reviews('','','', 'atracao-review',
    'https://www.tripadvisor.com.br/Attraction_Review-g303389-d4601254-Reviews-or5-Centro_Historico_de_Ouro_Preto-Ouro_Preto_State_of_Minas_Gerais.html',
    get_atracao_review_data,
    get_atracao_review_cards)
    print(f'tempo de execução: {(time.time() - start_time)/60} minutos')