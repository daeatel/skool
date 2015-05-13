#!/usr/bin/python
# encoding=utf-8

from rvp.items import RvpItem
from scrapy.contrib.spiders import Rule, CrawlSpider
# from scrapy.contrib.linkextractors import LinkExtractor
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
# from scrapy.http import Request
# from urlparse import urljoin


class RVPSpider(CrawlSpider):
    name = 'rvps'
    allowed_domains = ['odkazy.rvp.cz']
    start_urls = ['http://odkazy.rvp.cz/']
    rules = [Rule(SgmlLinkExtractor(allow=r'\/odkaz\/\w\/\d+\/[-\w]+\.html'), callback='parse_item'), Rule(SgmlLinkExtractor())]

    # def parse(self, response):
    #     for url in response.xpath("//a/@href").extract():
    #         yield Request(urljoin(response.url, url), callback=self.parse)

    def parse_item(self, response):
        item = RvpItem()
        item['url'] = response.xpath(
            "//table[@id='rodny_list_odkazu']/tr[2]/td/a/@href").extract()[0]
        item['author'] = response.xpath(
            "//table[@id='rodny_list_odkazu']/tr[1]/td/text()").extract()[0]
        item['name'] = response.xpath("//h3/text()").extract()[0]
        desc = response.xpath("//table[@id='rodny_list_odkazu']/tr[3]/td/text()").extract()
        if desc:
            item['description'] = desc[0]
        desc2 = response.xpath("//table[@id='rodny_list_odkazu']/tr[4]/td/text()").extract()
        if desc2:
            item['description2'] = desc2[0]
        item['published'] = response.xpath(
            "//div[@id='infobar_odkaz']/div/div[@class='homepage_right_box_inside']/text()").extract()[0]
        item['rating_rvp'] = response.xpath(
            "//div[@class='hodnoceni_popisek']/following-sibling::*/img/@alt")[0].extract()
        item['rating_users'] = response.xpath(
            "//div[@class='hodnoceni_popisek']/following-sibling::*/img/@alt")[1].extract()
        item['show'] = response.xpath(
            "//div[@id='infobar_odkaz']/div/div[@class='homepage_right_box_inside']/text()").extract()[1]
        item['categories'] = response.xpath(
            "//table[@id='rodny_list_odkazu']/tr[6]/td/ul/li").extract()
        item['lang'] = response.xpath(
            "//table[@id='rodny_list_odkazu']/tr[5]/td/text()").extract()[0]
        item['keywords'] = response.xpath(
            "//table[@id='rodny_list_odkazu']/tr[7]/td/a/text()").extract()
        item['image_urls'] = response.xpath(
            "//table[@id='rodny_list_odkazu']/tr[3]/td/a/img/@src").extract()
        return item

