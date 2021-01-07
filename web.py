from bs4 import BeautifulSoup
import requests
import json

#A partir de um link de hotel, entra na pagina do hotel em questão
#e extrai seus dados
def get_data_hotel(entry_link):
    entry_url = 'https://www.tripadvisor.com.br/' + entry_link
    r = requests.get(entry_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    nome = soup.find(id="HEADING").string.strip()
    print(nome)

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
        print(api_json)
        lat = "indef"
        lon = "indef"

    data = [nome, endereco, tipo, qtd_quartos, qtd_avaliacoes, nota, categoria, nota_pedestres, 
            restaurantes_perto, atracoes_perto, lat, lon, entry_url]
    #print(data)
    return data 

def get_data_restaurant(entry_link):
    entry_url = 'https://www.tripadvisor.com.br/' + entry_link
    r = requests.get(entry_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    nome = soup.find('h1', {'data-test-target':'top-info-header'}).string
    try:
        endereco = soup.find('a', {'class' : '_15QfMZ2L', 'href': '#MAPVIEW'}).string.replace(',',' |')
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
        faixa_preco = soup.find('div', class_='_1XLfiSsv').string.split('-')
        preco_min = faixa_preco[0].split()[1]
        preco_max = faixa_preco[1].split()[1]
    except:
        preco_min = 'indef'
        preco_max = 'indef'
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
    
    data = [nome, endereco, nota, avaliacoes, preco_min, preco_max, lat, lon, entry_url]
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

#Faz o parsing da página HTML que contém as listagens dos hotéis e retorna uma lista
#de links dos hotéis
def get_hotel_links(url):
    r = requests.get(url)
    html = r.text
    soup = BeautifulSoup(html, 'html.parser')
    listing_titles = soup.findAll(class_='listing_title')
    titles_links = []
    for entry in listing_titles:
        title_link = entry.find('a')['href']
        titles_links.append(title_link)

    return titles_links

def get_restaurants_links(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    restaurant_items = soup.findAll(class_='_1llCuDZj')
    restaurant_links = []
    for restaurant in restaurant_items:
        restaurant_link = restaurant.find('a')['href']
        restaurant_links.append(restaurant_link)
    
    return restaurant_links

#Gera, a partir de uma URl inicial, as URLS correspondentes ao avançar uma página na
#listagem
def get_page_urls(initial_url, url_to_offset, num_pages, entries_by_page):
    urls=[initial_url]
    data_offset = entries_by_page
    for _ in range(1,num_pages):
        url = url_to_offset.format(data_offset)
        urls.append(url)
        data_offset= data_offset + entries_by_page

    return urls

#Escreve os dados coletados (lista de listas) em um arquivo .csv
def write_to_file(filename, header, data):
    with open(filename, "w") as f:
        header_buffer = ",".join(header) + "\n"
        f.write(header_buffer)
        for instance in data:
            buffer = ",".join(instance)
            f.write(buffer+"\n")

#Retorna o numero de paginas de entradas
def get_max_num_pages(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    num_pages = soup.findAll('a', class_="pageNum")[-1].string
    return int(num_pages)

#Coleta e retorna os dados (lista de listas) dos hotéis a partir da URL inicial das listagens
def coleta_dados(initial_url, url_to_offset, get_links_function, data_extractor_function):
    num_pages = get_max_num_pages(initial_url)
    page_urls = get_page_urls(initial_url, url_to_offset, num_pages, 30)

    data = []
    #Seria bom utilizar multiprocessamento aqui
    for url in page_urls:
        links = get_links_function(url)
        d = list(map(data_extractor_function, links))
        data = data + d
    return data

if __name__ == "__main__":
    '''
    headers_hotel = ["nome", "endereço", "tipo", "qtd_quartos", "qtd_avaliacoes", "nota", "categoria", 
                "nota_pedesrtres", "restaurantes_perto", "atracoes_perto", "latitude", "longitude", "fonte"]

    hotel_initial_url = 'https://www.tripadvisor.com.br/Hotels-g303389-Ouro_Preto_State_of_Minas_Gerais-Hotels.html'
    hotel_url_to_offset = 'https://www.tripadvisor.com.br/Hotels-g303389-oa{}-Ouro_Preto_State_of_Minas_Gerais-Hotels.html'

    data_hoteis = coleta_dados(hotel_initial_url, hotel_url_to_offset, get_hotel_links, get_data_hotel)
    write_to_file("hoteis.csv", headers_hotel, data_hoteis)
    print(f'{len(data_hoteis)} hotéis coletados')
    '''

    restaurant_initial_url = 'https://www.tripadvisor.com.br/Restaurants-g303389-Ouro_Preto_State_of_Minas_Gerais.html'
    restaurant_url_to_offset = 'https://www.tripadvisor.com.br/RestaurantSearch-g303389-oa{}-Ouro_Preto_State_of_Minas_Gerais.html#EATERY_LIST_CONTENTS'
    data_restaurantes = coleta_dados(restaurant_initial_url, restaurant_url_to_offset, get_restaurants_links, get_data_restaurant)