# -*- coding: utf-8 -*-
from skool.utils import makepath

BOT_NAME = 'rvp'

SPIDER_MODULES = ['rvp.spiders']
NEWSPIDER_MODULE = 'rvp.spiders'
DOWNLOAD_DELAY = 0.3
DEPTH_LIMIT = 0
LOG_FILE = makepath('data/cats/log.txt')
FEED_URI = makepath('data/cats/output.json')
FEED_FORMAT = 'json'
ITEM_PIPELINES = {'rvp.pipelines.TreePipeline': 1}
