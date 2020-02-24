import json

import pandas as pd
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
        self.stations = {'li110460717s1620029748564158': {'name': '韦家碾站', 'line': '1号线(科学城-韦家碾)', 'href': 'https://cd.lianjia.com/ditiefang/li110460717s1620029748564158/'}}
        self.lst = []

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
            # proxy = self.get_proxy()
            # proxies = {
            #     'http': 'http://' + proxy,
            #     'https': 'https://' + proxy,
            # }
            page = requests.get(url, headers=self.headers)
            if page.status_code == 200:
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
                    page_line = requests.get(url_line, headers=self.headers)
                    soup_line = BeautifulSoup(page_line.text, "html.parser")
                    result_line = soup_line.find('div', {'data-role': 'ditiefang'})
                    content = result_line.find_all('div')[1].find_all('a')

                    for a_ele in content:
                        href = a_ele['href']
                        index = href.split('/')[2]
                        self.stations[index] = {
                            'name': a_ele.text,
                            'line': item['name'],
                            'href': "https://cd.lianjia.com" + href
                        }
                        print(self.stations)
            else:
                print('请求出错:' + page.status_code)
        except requests.ConnectionError:
            return None

    def get_house_by_station(self):
        for key, value in self.stations.items():
            url_stn = value['href']
            page_stn = requests.get(url_stn, headers=self.headers)
            soup_stn = BeautifulSoup(page_stn.text, "html.parser")
            try:  # 如果有多页数据，提取页码
                number = json.loads(soup_stn.find('div', {'class': 'page-box house-lst-page-box'})['page-data'])[
                    'totalPage']
            except:
                number = 1
                print('Number Error')

            station = value['name']
            line = value['line']

            print('正在爬取' + station)
            for i in range(1, number + 1):
                pg = ""
                if i > 1:
                    pg = "pg" + str(i)
                pg = requests.get(url_stn + pg, headers=self.headers)
                soup_dtl = BeautifulSoup(pg.text, "html.parser")
                result_dtl = soup_dtl.find('ul', {'class': 'sellListContent'})
                try:
                    first_result_dtl = result_dtl.find_all('li')  # 有些地铁站没有二手房信息，所以遇到这种情况程序需要自动跳过，否则会报错
                except:
                    print('无二手房信息')
                    continue

                for item in first_result_dtl:
                    title = item.find('div', {'class': 'title'}).find('a')
                    href = title['href']
                    housecode = title['data-housecode']
                    name = title.text
                    positionInfo = item.find('div', {'class': 'positionInfo'})
                    position_eles = positionInfo.findAll('a')
                    position = 'residential:' + position_eles[0].text + ';area:' + position_eles[1].text
                    houseInfo = item.find('div', {'class': 'houseInfo'})
                    house = houseInfo.text
                    followInfo = item.find('div', {'class': 'followInfo'})
                    follow = followInfo.text
                    tag = item.find('div', {'class': 'tag'})
                    tag_span = tag.find_all('span')
                    tags = []
                    for tag_item in tag_span:
                        tags.append(tag_item['class'][0] + ':' + tag_item.text)
                    unitPrice_ele = item.find('div', {'class': 'unitPrice'})
                    unitPrice = unitPrice_ele['data-price']
                    totalPrice_ele = item.find('div', {'class': 'totalPrice'})
                    totalPrice = totalPrice_ele.find('span').text
                    self.lst.append((housecode, name, line, station, position, house, follow, unitPrice, totalPrice,
                                     (';').join(tags), href))

    def save_to_csv(self):
        df = pd.DataFrame(self.lst,
                          columns=['housecode', 'name', 'line', 'station', 'position', 'house', 'follow', 'unitPrice',
                                   'totalPrice', 'tags', 'href'])
        df.to_csv('Lianjia_project.csv', index=False, encoding='utf-8')


if __name__ == '__main__':
    scrawl = Scrawl()
    # scrawl.get_lines_stations()
    scrawl.get_house_by_station()
    scrawl.save_to_csv()
