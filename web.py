from bs4 import BeautifulSoup
import requests
import json

#A partir de um link de hotel, entra na pagina do hotel em questão
#e extrai seus dados
def get_data_hotel(entry_link):
    entry_url = 'https://www.tripadvisor.com.br' + entry_link
    r = requests.get(entry_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    nome = soup.find(id="HEADING").string.strip()

    try:
        endereco = soup.find(class_='_3ErVArsu jke2_wbp').string.replace(","," |")
    except:
        endereco = "indef"
    #preco = soup.find("div", class_="CEf5oHnZ").string.split()[-1]
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

    data = [nome, endereco, tipo, qtd_quartos, qtd_avaliacoes, nota, categoria, nota_pedestres, 
            restaurantes_perto, atracoes_perto, lat, lon, entry_url]
    print(data)
    return data 

#A partir de um link de restaurante, entra na pagina e extrai os seus dados
def get_data_restaurant(entry_link):
    entry_url = 'https://www.tripadvisor.com.br' + entry_link
    r = requests.get(entry_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    nome = soup.find('h1', {'data-test-target':'top-info-header'}).string.replace(',', ' |')
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
    
    data = [nome, endereco, nota, avaliacoes, lat, lon, entry_url]
    print(data)
    return data

#A partir de um link de atracao, entra na pagina e extrai seus dados
def get_data_atracao(entry_link):
    entry_url = 'https://www.tripadvisor.com.br' + entry_link
    r = requests.get(entry_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    nome = soup.find('h1', id='HEADING').string.strip()
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
    
    data = [nome, endereco, nota, avaliacoes, lat, lon, entry_url]
    print(data)
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
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    listing_titles = soup.findAll(class_='listing_title')
    titles_links = []
    for entry in listing_titles:
        title_link = entry.find('a')['href']
        titles_links.append(title_link)

    return titles_links

#Retorna os links dos restaurantes presentes numa listagem
def get_restaurants_links(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    restaurant_items = soup.findAll(class_='_1llCuDZj')
    restaurant_links = []
    for restaurant in restaurant_items:
        restaurant_link = restaurant.find('a')['href']
        restaurant_links.append(restaurant_link)
    
    return restaurant_links

#Retorna os links das atracoes presentes numa listagem
def get_atracoes_links(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    atracoes_items = soup.findAll('a', class_='_1QKQOve4')
    atracoes_links = []
    for atracao in atracoes_items:
        atracao_link = atracao['href']
        atracoes_links.append(atracao_link)
    
    return atracoes_links

#Gera, a partir de uma URl inicial, as URLS correspondentes ao avançar uma página
def get_page_urls(initial_url, url_to_offset, num_pages, entries_by_page):
    urls=[initial_url]
    data_offset = entries_by_page
    for _ in range(1,num_pages):
        url = url_to_offset.format(data_offset)
        urls.append(url)
        data_offset= data_offset + entries_by_page

    return urls

#Escreve os dados coletados em um arquivo .csv
def write_to_file(filename, header, data):
    with open(filename, "w") as f:
        header_buffer = ",".join(header) + "\n"
        f.write(header_buffer)
        for instance in data:
            buffer = ",".join(instance)
            f.write(buffer+"\n")

#Retorna o numero de paginas total
def get_max_num_pages(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    num_pages = soup.findAll('a', class_="pageNum")[-1].string
    return int(num_pages)

#Retorna a proxima pagina na listagem de hoteis
def get_next_page_hoteis(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    next_page = soup.find('div', class_='ui_pagination').find('a', string='Próximas')['href']
    return next_page

#Retorna a proxima pagina na listagem de restaurantes
def get_next_page_restaurantes(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    next_page = soup.find('a', class_='nav next rndBtn ui_button primary taLnk')['href']
    return next_page

#Coleta e retorna os dados (lista de listas) de hoteis ou restaurantes a partir da URL inicial das listagens
def coleta_hoteis_ou_restaurantes(initial_url, data_extractor, get_links, get_next_page):
    url_to_collect = initial_url
    data = []
    while True:
        links = get_links(url_to_collect)
        d = list(map(data_extractor, links))
        data = data + d
        try:
            url_to_collect = 'https://www.tripadvisor.com.br' + get_next_page(url_to_collect)
        except:
            break

    return data

#Coleta e retorna os dados (lista de listas) de atracoes a partir da URL inicial das listagens
def coleta_atracoes(initial_url):
    num_pages = get_max_num_pages(initial_url)

    url_to_offset = initial_url.split('-')
    url_to_offset.insert(3, 'oa{}')
    url_to_offset = '-'.join(url_to_offset)

    page_urls = get_page_urls(initial_url, url_to_offset, num_pages, 30)

    data = []
    for url in page_urls:
        links = get_atracoes_links(url)
        d = list(map(get_data_atracao, links))
        data = data + d

    return data

def coleta_hoteis_e_escreve(url):
    headers_hotel = ["nome", "endereço", "tipo", "qtd_quartos", "qtd_avaliacoes", "nota", "categoria", 
                "nota_pedesrtres", "restaurantes_perto", "atracoes_perto", "latitude", "longitude", "fonte"]

    data_hoteis = coleta_hoteis_ou_restaurantes(url, get_data_hotel, get_hotel_links, get_next_page_hoteis)
    write_to_file("hoteis.csv", headers_hotel, data_hoteis)
    print(f'{len(data_hoteis)} hotéis coletados')

def coleta_restaurantes_e_escreve(url):
    headers_restaurant = ['nome', 'endereco', 'nota', 'avaliacoes', 'latitude', 'longitude', 'fonte']

    data_restaurantes = coleta_hoteis_ou_restaurantes(url, get_data_restaurant, get_restaurants_links, get_next_page_restaurantes)
    write_to_file('restaurantes.csv', headers_restaurant, data_restaurantes)
    print(f'{len(data_restaurantes)} restaurantes coletados')

def coleta_atracoes_e_escreve(url):
    headers_atracoes = ['nome', 'endereco', 'nota', 'avaliacoes', 'latitude', 'longitude', 'fonte']
    data_atracoes = coleta_atracoes(url)
    write_to_file('atracoes.csv', headers_atracoes, data_atracoes)
    print(f'{len(data_atracoes)} atracoes coletadas')

if __name__ == "__main__":
    hotel_url = 'https://www.tripadvisor.com.br/Hotels-g303389-Ouro_Preto_State_of_Minas_Gerais-Hotels.html'
    coleta_hoteis_e_escreve(hotel_url)
    
    restaurant_url = 'https://www.tripadvisor.com.br/Restaurants-g303389-Ouro_Preto_State_of_Minas_Gerais.html'
    coleta_restaurantes_e_escreve(restaurant_url)
    
    atracoes_url = 'https://www.tripadvisor.com.br/Attractions-g303389-Activities-a_allAttractions.true-Ouro_Preto_State_of_Minas_Gerais.html'
    coleta_atracoes_e_escreve(atracoes_url)