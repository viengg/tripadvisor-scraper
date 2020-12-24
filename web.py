from bs4 import BeautifulSoup
import requests

#A partir de um link de hotel, entra na pagina do hotel em questão
#e retorna seu nome, enderço, tipo e quantidade de quartos
def get_data(entry_link):
    entry_html = 'https://www.tripadvisor.com.br/' + entry_link
    r = requests.get(entry_html)
    soup = BeautifulSoup(r.text, 'html.parser')
    nome = soup.find(id="HEADING").string.strip()
    endereco = soup.find(class_='_3ErVArsu').string.replace(","," |")
    qtd_quartos = soup.find(attrs={'class':'_2t2gK1hs', 'data-tab':'TABS_ABOUT'}).findAll(class_="_1NHwuRzF")[-1].string

    if qtd_quartos is None:
        qtd_quartos = "indef"
    if "Pousada" in nome:
        tipo = "Pousada"
    elif "Hotel" in nome:
        tipo = "Hotel"
    elif "Hostel" in nome:
        tipo = "Hostel"
    else:
        tipo = "indef"
    
    data = [nome, endereco, tipo, qtd_quartos]
    print(data)
    return data 

#Faz o parsing da página HTML que contém as listagens dos hotéis e retorna uma lista
#de links dos hotéis
def parse_page(url):
    r = requests.get(url)
    html = r.text
    soup = BeautifulSoup(html, 'html.parser')
    listing_entries = soup.findAll(attrs={'data-ttpn': 'Hotels_MainList'})
    titles_links = []
    for entry in listing_entries:
        title_link = entry.find(class_='listing_title').find('a')['href']
        titles_links.append(title_link)

    return titles_links

#Gera, a partir de uma url inicial, as URLS correspondentes ao avançar uma página na
#listagem
def get_page_urls(initial_url, num_pages):
    urls=[initial_url]
    split_url = initial_url.split("-")
    num_entries_by_page = 30
    for i in range(1,num_pages):
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

#Coleta dados dos hotéis a partir da URL inicial das listagens
def coleta_hoteis(initial_url='https://www.tripadvisor.com.br/Hotels-g303389-Ouro_Preto_State_of_Minas_Gerais-Hotels.html'):
    page_urls = get_page_urls(initial_url, 3)

    data = []
    for url in page_urls:
        listing_titles = parse_page(url)
        d = list(map(get_data, listing_titles))
        data = data + d

    write_to_file("hoteis.csv",["nome", "endereço", "tipo", "qtd_quartos"], data)
    print(f'{len(data)} hotéis coletados')

if __name__ == "__main__":
    coleta_hoteis()