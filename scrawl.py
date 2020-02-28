import json
import re

import requests
from bs4 import BeautifulSoup

from save_data import SaveData

headers = {
    'Cache-Control': 'max-age=0',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
    'Connection': 'keep-alive',
    'Referer': 'https://cd.lianjia.com/ditiefang/'
}

none_housecode = 0


class Scrawl:
    none_housecode = 0
    # 'li1620045664386244s16000002378864'
    # https://cd.lianjia.com/ditiefang/li1620030075760238s1620030075760489/ie2dp4sf1mt2
    exclude_station_id = 'li1620045664386244s16000002378864'

    def __init__(self):
        self.lines = {}
        self.stations = []
        self.save = SaveData()

    def get_lines(self):
        url = 'https://cd.lianjia.com/ershoufang/'
        proxies = self.get_proxy()
        try:
            res = requests.get(url, headers=headers, proxies=proxies, timeout=15)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                result = soup.find('div', {'data-role': 'ditiefang'})
                if result is not None:
                    a_eles = result.find_all('a')
                    for item in a_eles:
                        href = item['href']
                        line = {
                            'name': item.text,
                            'href': "https://cd.lianjia.com" + href
                        }
                        self.lines[href.split('/')[2]] = line
                        # 获取当前线路的所有地铁站
                        self.get_stations(line)
                    print('line获取完毕', self.lines)
                    # 关闭数据库
                    self.mysqlDB.close_DB()
                else:
                    print('没有数据')
            else:
                print('请求出错:' + res.status_code)
                self.get_lines()
        except requests.ConnectionError:
            print('连接出错')
            self.get_lines()
            return None

    def get_stations(self, line):
        url_line = line['href']
        proxies = self.get_proxy()
        try:
            res = requests.get(url_line, headers=headers, proxies=proxies, timeout=15)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                result = soup.find('div', {'data-role': 'ditiefang'})
                a_eles = result.find_all('div')[1].find_all('a')

                for a_ele in a_eles:
                    href = a_ele['href']
                    index = href.split('/')[2]
                    station = {
                        'index': index,
                        'name': a_ele.text,
                        'line': line['name'],
                        'href': "https://cd.lianjia.com" + href
                    }
                    self.stations.append(station)
                    # 获取当前地铁站的所有二手房
                    self.get_house_by_station(station)
                print('station获取完毕', self.stations)
            else:
                print('请求出错:' + res.status_code)
                self.get_stations(line)
        except requests.ConnectionError:
            print('连接出错')
            self.get_stations(line)

    def get_condition(self):
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
        return paths

    def get_house_by_station(self, station):
        conditions = self.get_condition()
        stnname = station['name']
        line = station['line']
        # 按条件查询所有数据
        for condition in conditions:
            # 排除已经爬过的地铁站
            if self.exclude_station_id:
                if self.exclude_station_id != station['index']:
                    print('略过的地铁站', station['name'])
                    continue
                else:
                    if 'ie1dp1sf1mt2' == condition['path_str']:
                        self.exclude_station_id = None
                    print('略过的地铁站', station['name'], '条件', condition['path_str'])
                    continue

            url_stn = station['href']

            def format_data(item):
                title = item.find('div', {'class': 'title'}).find('a')
                href = title['href']
                if title.has_attr('data-housecode'):
                    housecode = title['data-housecode']
                elif title.has_attr('data-lj_action_housedel_id'):
                    housecode = title['data-lj_action_housedel_id']
                else:
                    self.none_housecode += 1
                    housecode = 'none-housecoe' + str(self.none_housecode)
                name = title.text
                positionInfo = item.find('div', {'class': 'positionInfo'})
                position_eles = positionInfo.findAll('a')
                residential = position_eles[0].text
                area = position_eles[1].text
                houseInfo = item.find('div', {'class': 'houseInfo'})
                info = houseInfo.text.split(' | ')
                type = info[0]
                houseArea = re.findall("\d*\.\d+|\d+", info[1])[0]
                orientation = info[2]
                decoration = info[3]
                floor = info[4]
                if '年' in info[5]:
                    buildingTime = re.findall("\d*\.\d+|\d+", info[5])[0]
                    buildingType = info[6]
                else:
                    buildingTime = None
                    buildingType = info[5]

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
                result = (
                    housecode, name, line, stnname, residential, area, type, float(houseArea), orientation,
                    decoration, floor, int(buildingTime) if buildingTime else None, buildingType, int(follow),
                    float(unitPrice), float(totalPrice), (';').join(tags), href
                )
                return result

            def get_house_by_page(page):
                house_list = []
                proxies = self.get_proxy()
                try:
                    res = requests.get(url_stn + page + condition['path_str'] + '/', headers=headers, proxies=proxies,
                                       timeout=15)
                    if res.status_code == 200:
                        soup_dtl = BeautifulSoup(res.text, "html.parser")
                        result_dtl = soup_dtl.find('ul', {'class': 'sellListContent'})
                        try:
                            house_li_eles = result_dtl.find_all('li')  # 有些地铁站没有二手房信息，所以遇到这种情况程序需要自动跳过，否则会报错
                        except:
                            print('无二手房信息')
                            return None
                        for item in house_li_eles:
                            house = format_data(item)
                            house += tuple(value for key, value in condition.items() if key != 'path_str')
                            house_list.append(house)
                        return house_list
                    else:
                        print('返回错误page', page)
                        return None
                except requests.ConnectionError:
                    print('连接出错, 重新查询')
                    get_house_by_page(page)

            proxy = self.get_proxy()
            try:
                print('正在爬取的地铁站和条件', url_stn + condition['path_str'])
                page_stn = requests.get(url_stn + condition['path_str'], headers=headers, proxies=proxy, timeout=15)
                if page_stn.status_code == 200:
                    soup_stn = BeautifulSoup(page_stn.text, "html.parser")
                    try:  # 如果有多页数据，提取页码
                        total_page = json.loads(
                            soup_stn.find('div', {'class': 'page-box house-lst-page-box'})['page-data']
                        )['totalPage']
                    except:
                        total_page = 1
                    # 分页查找
                    houses = []
                    for i in range(1, total_page + 1):
                        pg = ""
                        if i > 1:
                            pg = "pg" + str(i)
                        house_one_page = get_house_by_page(pg)
                        if house_one_page is not None:
                            print('当前页:', pg)
                            houses += house_one_page
                    if len(houses):
                        self.save_data(houses)
                else:
                    print('访问出错', page_stn.status_code)
            except requests.ConnectionError:
                print('请求出错地铁站', stnname)

    def get_proxy(self):
        def getOne():
            try:
                PROXY_POOL_URL = 'http://localhost:5555/get'
                response = requests.get(PROXY_POOL_URL)
                if response.status_code == 200:
                    return response.text
            except ConnectionError:
                return None

        ip = getOne()
        if ip is not None:
            proxy = {
                'http': 'http://' + ip
            }
            return proxy
        else:
            print('获取代理失败')
            return None

    def save_data(self, house_list):
        # if type == 'csv':
        #     save_data.save_to_csv(house_list)
        # else:
        self.save.save_to_csv(house_list)


if __name__ == '__main__':
    scrawl = Scrawl()
    scrawl.get_lines()
    # scrawl.get_house_by_station()
    # scrawl.save_data('mysql', [
    #     {'housecode': '106103984960', 'name': '天鹅湖北苑大标间，中楼层采光好，位置安静', 'line': '1号线(科学城-韦家碾)', 'station': '韦家碾站',
    #      'residential': '天鹅湖北苑 ', 'area': '新会展', 'type': '1室0厅 ', 'houseArea': ' 59.5平米 ', 'orientation': ' 南 ',
    #      'decoration': ' 简装 ', 'floor': ' 低楼层(共31层) ', 'buildingTime': ' 2007年建 ', 'buildingType': ' 板塔结合',
    #      'follow': '4', 'unitPrice': '14286', 'totalPrice': '85', 'tags': 'subway:近地铁;vr:VR房源;haskey:随时看房',
    #      'href': 'https://cd.lianjia.com/ershoufang/106103984960.html', 'elevator': 2, 'tradeProperty': 1,
    #      'farFromStation': 2}])
