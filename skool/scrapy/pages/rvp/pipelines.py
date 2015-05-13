# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import io
import re
import json
from skool.utils import makepath


class RvpPipeline(object):

    def open_spider(self, spider):
        self.langs = {}
        self.cnt = 1

    def process_item(self, item, spider):
        item['show'] = int(item['show'][11:-4])
        if item['show'] < 0:
            raise ValueError("Number of views is negative")
        # print item['show']

        if item['lang'] in self.langs:
            item['lang'] = self.langs[item['lang']]
        else:
            self.langs[item['lang']] = self.cnt
            self.cnt += 1
            item['lang'] = self.langs[item['lang']]
        if item['lang'] <= 0:
            raise ValueError("Language is zero or negative")
        if type(item['lang']) is not int:
            raise ValueError("Language is not integer")
        # print item['lang']

        item['rating_rvp'] = float(item['rating_rvp'][19:])
        if item['rating_rvp'] < 0 or item['rating_rvp'] > 5:
            raise ValueError("RVP rating is out of bounds (0-5)")
        # print item['rating_rvp']

        match = re.match(r'.*(\d\.\d+)', item['rating_users'])
        if match:
            item['rating_users'] = float(match.group(1))
        else:
            del item['rating_users']

        item['published'] = item['published'][13:]
        match = re.search(r'(\d+)\.\s(\d+)\.\s(\d+)', item['published'])
        md = int(match.group(1))
        mm = int(match.group(2))
        my = int(match.group(3))
        if md < 1 or md > 31 or mm < 1 or mm > 12 or my < 1951 or my > 2015:
            raise ValueError("Invalid date")
        print item['name'], " parsed"

        return item

    def close_spider(self, spider):
        print "Dumping langs to json"
        with io.open(makepath('data/langs.json'), 'w', encoding='utf-8') as f:
            f.write(unicode(json.dumps(self.langs, ensure_ascii=False)))
        print self.langs
        print "Done"
