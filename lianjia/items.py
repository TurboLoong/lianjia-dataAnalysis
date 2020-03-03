# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class HouseItem(scrapy.Item):
    collection = table = 'houses'
    keys = ['housecode', 'name', 'residential', 'area', 'type', 'houseArea',
            'orientation', 'decoration', 'floor', 'buildingTime', 'buildingType', 'follow',
            'unitPrice', 'totalPrice', 'tags', 'href', 'elevator', 'tradeProperty', 'farFromStation', 'station']
    # for key in keys:
    #     eval(key + ' = scrapy.Field()')
    housecode = scrapy.Field()
    name = scrapy.Field()
    residential = scrapy.Field()
    area = scrapy.Field()
    type = scrapy.Field()
    houseArea = scrapy.Field()
    orientation = scrapy.Field()
    decoration = scrapy.Field()
    floor = scrapy.Field()
    buildingTime = scrapy.Field()
    buildingType = scrapy.Field()
    follow = scrapy.Field()
    unitPrice = scrapy.Field()
    totalPrice = scrapy.Field()
    tags = scrapy.Field()
    href = scrapy.Field()
    elevator = scrapy.Field()
    tradeProperty = scrapy.Field()
    farFromStation = scrapy.Field()
    station = scrapy.Field()
