# TripAdvisor Scraper
Web-scraper para coleta de dados de hotéis, restaurantes e atrações de cidades a partir do seu link do TripAdvisor. Coleta tanto dados sobre os estabelecimentos quanto coleta os seus comentários.

# Como usar
Para o funcionamento do webscraper, é necessário fazer algumas modificações no código fonte (web.py):
1. Primeiro, é necessário inserir o link da página inicial de uma cidade e seu nome no objeto "cidades", localizado no final do arquivo na função "main".
2. Depois, se desejado, também é possível alterar algumas das constantes declaradas no ínicio do arquivo:
    - LANGUAGES_TO_COLLECT contém o array com os códigos do país da URL do TripAdvisor, que por sua vez determinará as linguagens dos comentários que serão coletados.
    - REQUEST_DELAY é o tempo em segundos que se espera antes de cada requisição GET.
    - COLLECT_UNTIL determina até que ano serão coletados comentários.
    - UPDATE_REVIEWS determina o modo de coleta dos comentários. Se é true, então os comentários serão atualizados, ao invés de coletar tudo desde o início.
    - TOO_MUCH_REVIEW_PAGES determina a partir de quantas páginas de comentários é realizada a filtragem de acordo com COLLECT_UNTIL. Essa filtragem é realizada utilizando uma busca binária, e é uma operação demorada.
    - NUM_THREADS_FOR_REVIEW e NUM_THREADS_FOR_PLACE determinam quantas threads são alocadas à coleta de reviews e à coleta de estabelecimentos, respectivamente. Cuidado aqui, pois o número de threads totais é de NUM_THREADS_FOR_PLACE + (NUM_THREADS_FOR_PLACE * NUM_THREADS_FOR_REVIEW).
    - HTML_PARSER determina o tipo de parser que é utilizado pelo BeautifulSoup.
3. Depois de configurado, basta rodar o arquivo web.py usando Python.
4. Depois de rodar o arquivo, algumas informações sobre o modo de coleta terão de ser inseridas pela CLI:
    - O modo de coleta é determinado por uma string com os números 1, 2 e 3, correspondentes à coleta dos hóteis, restaurantes e atrações, respectivamente. Caso deseje coletar mais de um tipo de estabelecimento de uma vez, basta inserir o símbolo correspondente. Por exemplo, a coleta de somente hóteis é determinada pela string "1", de hóteis e atrações pela string "13", e de hóteis, restaurantes e atrações pela string "123".
    - Depois, é possível determinar se os comentários serão coletados.
5. Ao final da coleta, os arquivos .csv gerados serão salvos em uma pasta com o nome da cidade.

# Clean.py
Caso esteja com processos "zumbi" criados pela execução do coletor, utilize o arquivo clean.py para excluí-los. (ATENÇÃO: a execução do arquivo também irá fechar todas as instâncias do Chrome abertas)

