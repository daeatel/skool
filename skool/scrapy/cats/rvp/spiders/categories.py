#!/usr/bin/python
# encoding=utf-8

from rvp.items import TreeItem
from scrapy.contrib.spiders import Rule, CrawlSpider
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor


class CatSpider(CrawlSpider):
    name = 'cats'
    allowed_domains = ['odkazy.rvp.cz']
    start_urls = ['http://odkazy.rvp.cz/']
    rules = [Rule(SgmlLinkExtractor(allow=r'\/odkazy\/[\w]+\/[-\w]+\.html$'), callback='parse_item', follow=True)]

    def parse_item(self, response):
        # print "PARSING ", response.url
        item = TreeItem()
        # 6::2 - 6-skip initial toplevel categories, 2 - skip &gt elements
        item['text'] = response.xpath(
            "//div[@id='drob_navigace']//text()").extract()[6::2]
        item['pagetitle'] = response.xpath("//title//text()").extract()[0][48:].strip()
        return item
