# -*- coding: utf-8 -*-

# Scrapy settings for rvp project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#
from skool.utils import makepath

BOT_NAME = 'rvp'

SPIDER_MODULES = ['rvp.spiders']
NEWSPIDER_MODULE = 'rvp.spiders'
DOWNLOAD_DELAY = 0.3
DEPTH_LIMIT = 0
LOG_FILE = makepath('data/pages/log.txt')
FEED_URI = makepath('data/pages/output.json')
FEED_FORMAT = 'json'
ITEM_PIPELINES = {'rvp.pipelines.RvpPipeline': 1}

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'rvp (+http://www.yourdomain.com)'
