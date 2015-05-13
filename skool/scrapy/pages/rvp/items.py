# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy import Field, Item


class RvpItem(Item):
    url = Field()
    author = Field()
    name = Field()
    description = Field()
    description2 = Field()
    published = Field()
    rating_rvp = Field()
    rating_users = Field()
    show = Field()
    categories = Field()
    lang = Field()
    keywords = Field()
    image_urls = Field()
    images = Field()
