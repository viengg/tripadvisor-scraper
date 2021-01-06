from bs4 import BeautifulSoup
import requests

#A partir de um link de hotel, entra na pagina do hotel em questão
#e retorna seu nome, enderço, tipo e quantidade de quartos
def get_data_hotel(entry_link):
    entry_url = 'https://www.tripadvisor.com.br/' + entry_link
    r = requests.get(entry_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    nome = soup.find(id="HEADING").string.strip()
    endereco = soup.find(class_='_3ErVArsu').string.replace(","," |")
    #preco = soup.find("div", class_="CEf5oHnZ").string.split()[-1]
    qtd_avaliacoes = soup.find("span", class_='_33O9dg0j').string.split()[0]
    nota = soup.find("span", class_="_3cjYfwwQ").string.replace(",", ".")
    nota_pedestres = soup.find("span", class_="oPMurIUj _1iwDIdby").string
    restaurantes_perto = soup.find("span", class_="oPMurIUj TrfXbt7b").string
    atracoes_perto = soup.find("span", class_="oPMurIUj _1WE0iyL_").string
    try:
        categoria = soup.find("svg", class_="_2aZlo29m")['title'].split()[0].replace(",", ".")
    except:
        categoria = "indef"
    qtd_quartos = soup.find(attrs={'class':'_2t2gK1hs', 'data-tab':'TABS_ABOUT'}).findAll(class_="_1NHwuRzF")[-1].string
    if qtd_quartos is None:
        qtd_quartos = "indef"
    tipo = get_type_by_name(nome, ['Hotel', 'Pousada', 'Hostel'])
    
    data = [nome, endereco, tipo, qtd_quartos, qtd_avaliacoes, nota, categoria, nota_pedestres, 
            restaurantes_perto, atracoes_perto, entry_url]
    print(data)
    return data 

#Infere o tipo a partir do nome do hotel
def get_type_by_name(name, possible_types):
    for tipo in possible_types:
        if tipo in name:
            return tipo
    return "indef"

#Faz o parsing da página HTML que contém as listagens dos hotéis e retorna uma lista
#de links dos hotéis
def get_hotel_links(url):
    r = requests.get(url)
    html = r.text
    soup = BeautifulSoup(html, 'html.parser')
    listing_entries = soup.findAll(attrs={'data-ttpn': 'Hotels_MainList'})
    titles_links = []
    for entry in listing_entries:
        title_link = entry.find(class_='listing_title').find('a')['href']
        titles_links.append(title_link)

    return titles_links

#Gera, a partir de uma URl inicial, as URLS correspondentes ao avançar uma página na
#listagem
def get_page_urls(initial_url, num_pages):
    urls=[initial_url]
    split_url = initial_url.split("-")
    num_entries_by_page = 30
    for _ in range(1,num_pages):
        aux = "oa" + str(num_entries_by_page)
        url = split_url[:]
        url.insert(2, aux)
        url = '-'.join(url)
        urls.append(url)
        num_entries_by_page = num_entries_by_page + num_entries_by_page

    return urls

#Escreve os dados coletados (lista de listas) em um arquivo .csv
def write_to_file(filename, header, data):
    with open(filename, "w") as f:
        header_buffer = ",".join(header) + "\n"
        f.write(header_buffer)
        for instance in data:
            buffer = ",".join(instance)
            f.write(buffer+"\n")

#Coleta e retorna os dados (lista de listas) dos hotéis a partir da URL inicial das listagens
def coleta_hoteis(initial_url='https://www.tripadvisor.com.br/Hotels-g303389-Ouro_Preto_State_of_Minas_Gerais-Hotels.html'):
    page_urls = get_page_urls(initial_url, 3)

    data = []
    #Seria bom utilizar multiprocessamento aqui
    for url in page_urls:
        hotel_links = get_hotel_links(url)
        d = list(map(get_data_hotel, hotel_links))
        data = data + d
    return data

if __name__ == "__main__":
    headers_hotel = ["nome", "endereço", "tipo", "qtd_quartos", "qtd_avaliacoes", "nota", "categoria", 
                "nota_pedesrtres", "restaurantes_perto", "atracoes_perto", "fonte"]
    data = coleta_hoteis()
    write_to_file("hoteis.csv", headers_hotel, data)
    print(f'{len(data)} hotéis coletados')