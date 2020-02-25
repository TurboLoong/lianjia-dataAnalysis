import json
import re

import requests
from bs4 import BeautifulSoup

from save_data import SaveToMysql

headers = {
    'Cache-Control': 'max-age=0',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
    'Connection': 'keep-alive',
    'Referer': 'https://cd.lianjia.com/ditiefang/'
}


class Scrawl:
    def __init__(self):
        self.lines = {}
        self.stations = {'li110460717s1620029748564158': {
            'name': '韦家碾站', 'line': '1号线(科学城-韦家碾)',
            'href': 'https://cd.lianjia.com/ditiefang/li110460717/'
        }}

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
            page = requests.get(url, headers=headers)
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
                    page_line = requests.get(url_line, headers=headers)
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
            # 有无电梯 elevator
            ies = [{'index': 'ie2', 'value': 2}, {'index': 'ie1', 'value': 1}]
            # 交易权属 tradeProperty
            dps = [{'index': 'dp1', 'value': 1},
                   {'index': 'dp2', 'value': 2},
                   {'index': 'dp3', 'value': 3},
                   {'index': 'dp4', 'value': 4}]
            sf = [{'index': 'sf1', 'value': '普通住宅'}]
            # 地铁距离 farFromStation
            mts = [{'index': 'mt1', 'value': 1}, {'index': 'mt2', 'value': 2},
                   {'index': 'mt3', 'value': 3}]

            # 构造所有的条件查询
            paths = []
            path_temp = {}
            for ie in ies:
                path_temp['elevator'] = ie['value']
                for dp in dps:
                    path_temp['tradeProperty'] = dp['value']
                    for mt in mts:
                        path_temp['farFromStation'] = mt['value']
                        path_temp['path_str'] = ('ie' + str(ie['value'])) + \
                                                ('dp' + str(dp['value']) + str(sf[0]['index'])) + \
                                                ('mt' + str(mt['value']))
                        paths.append({key: value for key, value in path_temp.items()})
            print('paths:-------', paths)
            paths = [paths[0], paths[1], paths[2]]
            # 按条件查询所有数据
            for path in paths:
                url_stn = value['href']
                page_stn = requests.get(url_stn + path['path_str'], headers=headers)
                soup_stn = BeautifulSoup(page_stn.text, "html.parser")
                try:  # 如果有多页数据，提取页码
                    total_page = json.loads(
                        soup_stn.find('div', {'class': 'page-box house-lst-page-box'})['page-data']
                    )['totalPage']
                except:
                    total_page = 1
                    print('Number Error')

                station = value['name']
                line = value['line']
                print('正在爬取:', path)
                total_page = 1

                # 分页查找
                house_list = []
                for i in range(1, total_page + 1):
                    pg = ""
                    if i > 1:
                        pg = "pg" + str(i)
                    pg = requests.get(url_stn + pg + path['path_str'] + '/', headers=headers)
                    soup_dtl = BeautifulSoup(pg.text, "html.parser")
                    result_dtl = soup_dtl.find('ul', {'class': 'sellListContent'})
                    try:
                        house_li_eles = result_dtl.find_all('li')  # 有些地铁站没有二手房信息，所以遇到这种情况程序需要自动跳过，否则会报错
                    except:
                        print('无二手房信息')
                        continue

                    for item in house_li_eles:
                        house = self.format_data(item, station, line)
                        house.update({key: value for key, value in path.items() if key != 'path_str'})
                        house_list.append(house)
                print(house_list)
                self.save_data('mysql', house_list)

    def format_data(self, item, station, line):
        title = item.find('div', {'class': 'title'}).find('a')
        href = title['href']
        housecode = title['data-housecode']
        name = title.text
        positionInfo = item.find('div', {'class': 'positionInfo'})
        position_eles = positionInfo.findAll('a')
        residential = position_eles[0].text
        area = position_eles[1].text
        houseInfo = item.find('div', {'class': 'houseInfo'})
        house = houseInfo.text.split(' | ')
        print(house)
        type = house[0]
        houseArea = re.findall("\d*\.\d+|\d+", house[1])[0]
        orientation = house[2]
        decoration = house[3]
        floor = house[4]
        try:
            if '年' in house[5]:
                buildingTime = re.findall("\d*\.\d+|\d+", house[5])[0]
                buildingType = house[6]
            else:
                buildingTime = None
                buildingType = house[5]
        except:
            print(house)
            return None
        followInfo = item.find('div', {'class': 'followInfo'})
        follow = followInfo.text[0]
        tag = item.find('div', {'class': 'tag'})
        tag_span = tag.find_all('span')
        tags = []
        for tag_item in tag_span:
            tags.append(tag_item['class'][0] + ':' + tag_item.text)
        unitPrice_ele = item.find('div', {'class': 'unitPrice'})
        unitPrice = unitPrice_ele['data-price']
        totalPrice_ele = item.find('div', {'class': 'totalPrice'})
        totalPrice = totalPrice_ele.find('span').text
        result = {
            'housecode': housecode, 'name': name, 'line': line, 'station': station, 'residential': residential,
            'area': area, 'type': type, 'houseArea': float(houseArea), 'orientation': orientation,
            'decoration': decoration, 'floor': floor, 'buildingTime': int(buildingTime) if buildingTime else None, 'buildingType': buildingType,
            'follow': int(follow), 'unitPrice': float(unitPrice), 'totalPrice': float(totalPrice),
            'tags': (';').join(tags), 'href': href
        }
        return result

    def save_data(self, type, house_list):
        save_data = SaveToMysql(type)
        if type == 'csv':
            save_data.save_to_csv(house_list)
        else:
            save_data.save_to_mysql(house_list)


if __name__ == '__main__':
    scrawl = Scrawl()
    # scrawl.get_lines_stations()
    scrawl.get_house_by_station()
    # scrawl.save_data('mysql', [
    #     {'housecode': '106103984960', 'name': '天鹅湖北苑大标间，中楼层采光好，位置安静', 'line': '1号线(科学城-韦家碾)', 'station': '韦家碾站',
    #      'residential': '天鹅湖北苑 ', 'area': '新会展', 'type': '1室0厅 ', 'houseArea': ' 59.5平米 ', 'orientation': ' 南 ',
    #      'decoration': ' 简装 ', 'floor': ' 低楼层(共31层) ', 'buildingTime': ' 2007年建 ', 'buildingType': ' 板塔结合',
    #      'follow': '4', 'unitPrice': '14286', 'totalPrice': '85', 'tags': 'subway:近地铁;vr:VR房源;haskey:随时看房',
    #      'href': 'https://cd.lianjia.com/ershoufang/106103984960.html', 'elevator': 2, 'tradeProperty': 1,
    #      'farFromStation': 2}])
