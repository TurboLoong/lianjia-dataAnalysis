# -*- coding: utf-8 -*-
import json
import re

from bs4 import BeautifulSoup
from scrapy import Spider, Request

from ..items import HouseItem


class ErshoufangSpider(Spider):
    name = 'ershoufang'
    allowed_domains = ['cd.lianjia.com']
    start_urls = ['https://cd.lianjia.com/ershoufang/']

    def parse(self, response):
        line_links = response.xpath('//div[@data-role="ditiefang"]//a/@href').extract()
        # for link in line_links:
        #     yield Request(url=response.urljoin(link), callback=self.lines_parse)
        link = line_links[0]
        print('parse', response.urljoin(link))
        yield Request(url=response.urljoin(link), callback=self.lines_parse)

    def lines_parse(self, response):
        station_links = response.xpath('//div[@data-role="ditiefang"]/div[2]/a/@href').extract()
        station_names = response.xpath('//div[@data-role="ditiefang"]/div[2]/a/text()').extract()
        conditions = self.get_condition()
        for link, name in tuple(zip(station_links, station_names))[:1]:
            for condition in conditions[:2]:
                print('lines_parse', response.urljoin(link + condition['path_str'] + '/'))
                yield Request(url=response.urljoin(link + condition['path_str'] + '/'), callback=self.station_parse,
                              meta={'station': name, 'condition': condition, 'path': link})

    def station_parse(self, response):
        condition = response.meta['condition']
        total = int(response.xpath('//h2[@class="total fl"]/span/text()').extract_first().strip())
        if total:
            total_page_obj = response.xpath('//div[@class="page-box house-lst-page-box"]/@page-data').extract_first()
            if total_page_obj:
                total_page = json.loads(total_page_obj)['totalPage']
            else:
                total_page = 1
            for i in range(1, total_page + 1):
                if i > 1:
                    pg = 'pg' + str(i)
                    yield Request(
                        'https://' + self.allowed_domains[0] + response.meta['path'] + pg + condition['path_str'] + '/',
                        callback=self.get_house_by_page,
                        meta=response.meta)
                else:
                     self.get_house_by_page(response)
        else:
            pass

    def get_house_by_page(self, response):
        keys = ('housecode', 'name', 'residential', 'area', 'type', 'houseArea',
                'orientation', 'decoration', 'floor', 'buildingTime', 'buildingType', 'follow',
                'unitPrice', 'totalPrice', 'tags', 'href', 'elevator', 'tradeProperty', 'farFromStation', 'statioin')
        condition = response.meta['condition']
        station = response.meta['station']
        body = response.text
        result_ul = BeautifulSoup(body, 'html.parser')
        house_list_eles = result_ul.find('ul', {'class': 'sellListContent'})
        house_li_eles = house_list_eles.find_all('li')
        for item in house_li_eles:
            house = self.format_data(item)
            house += tuple(value for key, value in condition.items() if key != 'path_str')
            house += tuple(station)
            for key, value in tuple(zip(keys, house)):
                result = HouseItem()
                result[key] = value
            yield result

    def get_condition(self):
        # 有无电梯 elevator
        ies = [{'index': 'ie2', 'value': 2}]
        # ies = [{'index': 'ie2', 'value': 2}, {'index': 'ie1', 'value': 1}]
        # 交易权属 tradeProperty
        dps = [{'index': 'dp1', 'value': 1},
               {'index': 'dp2', 'value': 2},
               {'index': 'dp3', 'value': 3},
               {'index': 'dp4', 'value': 4}]
        sf = [{'index': 'sf1', 'value': '普通住宅'}]
        # 地铁距离 farFromStation
        mts = [{'index': 'mt1', 'value': 1}, {'index': 'mt2', 'value': 2}]
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

    def format_data(self, item):
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
            housecode, name, residential, area, type, float(houseArea), orientation,
            decoration, floor, int(buildingTime) if buildingTime else None, buildingType, int(follow),
            float(unitPrice), float(totalPrice), (';').join(tags), href
        )
        return result
