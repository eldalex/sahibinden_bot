import random
import string
import time
import requests
from bs4 import BeautifulSoup

# Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.63
# czIqF6i52e9rPAXC6336c819
class Sahibinden_parser():
    def __init__(self, database):
        self.db = database
        self.headers = self.get_headers()

    def get_headers(self):
        return {
            'Cookie': 'cdid=MX7v0heJhdzls20u63eb7d30; csid=sFfB3UNNp3icBrVg5SXU2jPuXJqD0rHILkECPnBaXNFvq3hP5UB2lWRW2D7KfgmNWk0LqnTU6gknInB/G/h2P9+eHYH6YuYiAygBfoBkFXJs3abeUNw+gZyLI6AzyBUO2ldILO61Igp64OLTkIVRgDOmt0qRb5A/JCciOiJA1KVfO9t2euOx4EPUTHxPujmF; nwsh=std; st=a315fd26a0b39403ba27f64082311d2c3a9e39e1b483fcdd6190a543f69347eb50993fc142f3c0eb7a01f65ddafd550f7e5fe2766ad2b9bc3; vid=193',
            'Host': 'www.sahibinden.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }

    def get_one_app(self, html):
        try:
            link = f"https://www.sahibinden.com{html.find('a').get('href')}"
            thumbnail_url = html.find('a').find('img').get('src')
            id = link.split('/')[-2].split('-')[-1]
            all_info = html.findAll('td')
            area = all_info[2].text.strip()
            rooms = all_info[3].text.strip()
            price = all_info[4].text.strip()
            date_listing = ' '.join(all_info[5].text.replace('\n', '').split())
            district = all_info[6].text.strip()
            return {
                'id': id,
                'link': link,
                'thumbnail_url': thumbnail_url,
                'area': area,
                'rooms': rooms,
                'price': price,
                'date_listing': date_listing,
                'district': district
            }
        except:
            pass

    def get_current_url_appartments(self, URL):
        try:
            all_apps = []
            offset = 0
            rental_announcements = requests.get(URL, headers=self.headers)
            if rental_announcements.status_code == 200:
                soup = BeautifulSoup(rental_announcements.text, 'html5lib')
                count_html = soup.find('div', {'class': 'resultsTextWrapper'})
                if count_html.find('span'):
                    count_announcements = int(count_html.find('span').text.split(' ')[0])
                else:
                    count_announcements = -1
                while offset <= count_announcements:
                    offset_url = f'{URL}pagingOffset={offset}'
                    offset += 50
                    rental_announcements = requests.get(offset_url, headers=self.headers)
                    soup = BeautifulSoup(rental_announcements.text, 'html5lib')
                    announcements_html = soup.findAll('tr', {'class': 'searchResultsItem'})
                    for announcement in announcements_html:
                        all_apps.append(self.get_one_app(announcement))
                    for i in range(random.randint(7, 15), -1, -1):
                        print(f'спим ещё {i} секунд')
                        time.sleep(1)
                for i in range(len(all_apps) - 1, -1, -1):
                    if all_apps[i] is None:
                        all_apps.pop(i)
                return all_apps
            else:
                raise Exception('Responce not 200')
        except Exception as ex:
            print(f'Ошибка!!! {ex}')

    def get_current_user_find_urls(self, user_id):
        return self.db.get_user_urls(user_id)

    def get_all_results_distinct(self, all_results):
        distinct_id = []
        all_results_distinct = []
        for result in all_results:
            # Результаты поиска могут пересекаться, так что оставляем только уникальные
            if result['id'] not in distinct_id:
                all_results_distinct.append(result)
                distinct_id.append(result['id'])
        return all_results_distinct, distinct_id

    def get_all_results(self, urls):
        all_results = []
        for url in urls:
            # Собираем все результаты по всем трем поискам в один список
            for i in range(random.randint(5, 10), -1, -1):
                print(f'Перед следующим фильтром спим ещё {i} секунд')
                time.sleep(1)
            all_results.extend(self.get_current_url_appartments(url))

        return all_results

    def start_search(self, user_id):
        try:
            # Извлекаем url для поиска (у каждого пользователя до трех штук)
            all_results = []
            distinct_id = []
            all_results_distinct = []
            urls = self.get_current_user_find_urls(user_id)
            all_results = self.get_all_results(urls)
            all_results_distinct, distinct_id = self.get_all_results_distinct(all_results)
            # так как все результаты хранятся в одной таблице с идентификатором по номеру объявления, результаты разных пользователей могут пересекаться
            # отправляем их на дополнительную фильтрацию, и запишем только те что еще не присутствуют в БД
            all_results_distinct = self.db.get_only_new_results(all_results_distinct)
            if all_results_distinct:
                # Отправляем полученный список уникальных объявлений в БД
                self.db.save_all_result_to_base(all_results_distinct)
                # Отправляем id объявлений в результат поиска пользователя
                self.db.save_all_id_for_user(distinct_id, user_id)
            return True
        except Exception as ex:
            print(ex)

    def generate_coocies(self):
        cdid=''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits) for _ in range(24))
        csid=''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase + string.digits+'/') for _ in range(192))
        nwsh = 'std'
        st=''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(113))
        vid=''.join(random.choice('123456789') for _ in range(3))
        # return f'cdid={cdid}; csid={csid}; nwsh={nwsh}; vid={vid}'
        return f'cdid={cdid}; csid={csid}; nwsh={nwsh}; vid={vid}'


    def get_user_agent(self):
        user_agents=[
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.63',
            'Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0',
            'Mozilla/5.0 (X11; Linux x86_64) KHTML/4.14.8 (like Gecko) Konqueror/4.14 Fedora/4.14.8-13.el7'
        ]
        return user_agents[random.randint(0,3)]

    def generate_headers(self):
        return {
            'Cookie': self.generate_coocies(),
            'Host': 'www.sahibinden.com',
            'User-Agent': self.get_user_agent(),
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }

    def test_get_data(self):
        url='https://www.sahibinden.com/kiralik-daire?date=1day&pagingSize=50&a812=40728&a812=40602&a812=40603&a812=40604&a812=40605&a812=40606&a20=38473&a20=1206094&a20=1213206&a20=38470&a20=1259450'
        headers=self.generate_headers()
        rental_announcements = requests.get(url, headers=headers)
        soup = BeautifulSoup(rental_announcements.text, 'html5lib')
        print('stop')

    #'Cookie': '
# cdid=MX7v0heJhdzls20u63eb7d30;
# csid=sFfB3UNNp3icBrVg5SXU2jPuXJqD0rHILkECPnBaXNFvq3hP5UB2lWRW2D7KfgmNWk0LqnTU6gknInB/G/h2P9+eHYH6YuYiAygBfoBkFXJs3abeUNw+gZyLI6AzyBUO2ldILO61Igp64OLTkIVRgDOmt0qRb5A/JCciOiJA1KVfO9t2euOx4EPUTHxPujmF;
# nwsh=std;
# st=a315fd26a0b39403ba27f64082311d2c3a9e39e1b483fcdd6190a543f69347eb50993fc142f3c0eb7a01f65ddafd550f7e5fe2766ad2b9bc3;
# vid=193',