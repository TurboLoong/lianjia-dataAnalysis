# -*- coding: utf-8 -*-
from scrapy import Spider


class ErshoufangSpider(scrapy.Spider):
    name = 'ershoufang'
    allowed_domains = ['cd.lianjia.com']
    start_urls = ['http://cd.lianjia.com/ershoufang/']

    def parse(self, response):
        line_links = response.xpath('//div[@data-role="ditiefang"]//a/@href').extract()

        yield

    def lines_parse(self, response):

    def stations_parse(self, response):