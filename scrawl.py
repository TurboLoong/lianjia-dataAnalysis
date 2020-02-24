import json

import requests
from bs4 import BeautifulSoup


class Scrawl:
    headers = {
        'Cache-Control': 'max-age=0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
        'Connection': 'keep-alive',
        'Referer': 'https://cd.lianjia.com/ditiefang/'
    }

    def __init__(self):
        self.lines = {}
        self.stations = {}

    def get_proxy(self):
        try:
            PROXY_POOL_URL = 'http://localhost:5555/get'
            response = requests.get(PROXY_POOL_URL)
            if response.status_code == 200:
                return response.text
        except ConnectionError:
            return None

    def get_lines_stations(self):

        url = 'https://cd.lianjia.com/ershoufang/'
        try:
            proxy = self.get_proxy()
            proxies = {
                'http': 'http://' + proxy,
                'https': 'https://' + proxy,
            }
            page = requests.get(url, headers=scrawl.headers)
            soup = BeautifulSoup(page.text, "html.parser")
            result = soup.find('div', {'data-role': 'ditiefang'})
            a_eles = result.find_all('a')
            for item in a_eles:
                href = item['href']
                self.lines[href.split('/')[2]] = {
                    'name': item.text,
                    'href': "https://cd.lianjia.com" + href
                }

            for item in self.lines.values():
                url_line = item['href']
                page_line = requests.get(url_line, headers=scrawl.headers)
                soup_line = BeautifulSoup(page_line.text, "html.parser")
                result_line = soup_line.find('div', {'data-role': 'ditiefang'})
                content = result_line.find_all('div')[1].find_all('a')

                for a_ele in content:
                    href = a_ele['href']
                    index = href.split('/')[2]
                    if index not in self.stations.keys():
                        self.stations[index] = {
                            'name': a_ele.text,
                            'href': "https://cd.lianjia.com" + href
                        }
                    else:
                        continue

            print(self.lines)
            print(self.stations)
        except requests.ConnectionError:
            return None

    def get_house_by_station(self):
        lst = []  # 将所有提取的二手房信息全部储存到lst中
        for key, value in self.stations:
            url_stn = value.href
            page_stn = requests.get(url_stn, )
            soup_stn = BeautifulSoup(page_stn.text, "html.parser")
            try:  # 如果有多页数据，提取页码
                number = json.loads(soup_stn.find('div', {'class': 'page-box house-lst-page-box'})['page-data'])[
                    'totalPage']
            except:
                number = 1
                print('Number Error')

            stn_name = value.name
            ln_name = self.lines[stn_name]

            print('正在爬取' + stn_name)

            for i in range(1, number + 1):
                pg = ""
                if i > 1:
                    pg = "pg" + str(i)
                pg = requests.get(url_stn + pg)
                soup_dtl = BeautifulSoup(pg.text, "html.parser")
                result_dtl = soup_dtl.find('ul', {'class': 'sellListContent'})
                try:
                    first_result_dtl = result_dtl.find_all('li')  # 有些地铁站没有二手房信息，所以遇到这种情况程序需要自动跳过，否则会报错
                except:
                    print('无二手房信息')
                    continue

                for item in first_result_dtl:
                    house = item.find('div', {'class': 'houseInfo'})
                    rsd = house.text
                    condition = item.find('div', {'class': 'positionInfo'})
                    age = condition.text
                    Pr = item.find('div', {'class': 'unitPrice'})
                    price = Pr.text
                    Tlpr = item.find('div', {'class': 'totalPrice'})
                    ttlprice = Tlpr.text
                    lst.append((ln_name, stn_name, rsd, age, price, ttlprice))
            print(len(lst))


if __name__ == '__main__':
    scrawl = Scrawl()
    scrawl.get_lines_stations()
