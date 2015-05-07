#!/usr/bin/python
# encoding=utf-8
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy.utils.project import get_project_settings
from scrapy.xlib.pydispatch import dispatcher
from scrapy.http import Request, HtmlResponse
from scrapy.item import Item, Field
from scrapy.crawler import Crawler
from scrapy.spider import Spider
from scrapy import log, signals
from twisted.internet import reactor
import datetime
import urlparse
import re
import lmdb
import pytz
import iso8601
import justext
import xmlrpclib
import urllib2

from models import Page, Site, Label

DB_PATH = '/tmp/dbtest'
now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)


def open_env():
    return lmdb.open(DB_PATH, max_dbs=1)


def rebuild_url_lookup():
    print "Rebuilding URL"
    env = open_env()
    urls = env.open_db('urls')
    with env.begin(db=urls, write=True) as txn:
        cursor = txn.cursor()
        for k, v in cursor:
            txn.delete(k)
        for item in Page.objects():
            t = item.url.encode('utf-8')
            if 'gvh' in t:
                print t
            txn.put(t, '1')
    print "Done"
    env.close()


env = open_env()

rebuild = False
with env.begin(write=True) as txn:
    tres = txn.get('lastdate')
    print tres
    if tres:
        res = iso8601.parse_date(tres)
        res.replace(tzinfo=pytz.utc)
        delta = now - res
        if delta > datetime.timedelta(days=1):
            rebuild = True
    else:
        rebuild = True
    txn.put('lastdate', now.isoformat())

    if rebuild:
        rebuild_url_lookup()
    else:
        print "URLs OK"

env.close()


def add_to_lookup(url):
    env = open_env()
    urls = env.open_db('urls')
    with env.begin(db=urls, write=True) as txn:
        txn.put(url.encode('utf-8'), '1')
    env.close()


def addtodb(page, lookupurl, classes):
    parent = Site.objects(url=lookupurl).first()
    nov = Page(url=page['url'], btext=page['btext'])
    if parent:
        nov.parent = parent
    for c in classes:
        label = Label.objects(id=c).first()
        nov.label_model.append(label)
        print "label added"
    nov.save()
    add_to_lookup(page['url'])
    print "Page added to db"

client = xmlrpclib.ServerProxy('http://localhost:8001', allow_none=True)


def crawl_page(url, parenturl=None):
    if not newurl(url):
        return
    # if not parenturl:
    #     parsed = urlparse.urlparse(url)
    #     parenturl = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed)
    res = []
    response = urllib2.urlopen(url)
    body = response.read()
    paragraphs = justext.justext(body, justext.get_stoplist("Czech"))
    for para in paragraphs:
        if not para.is_boilerplate:
            res.append(para.text)
    btext = ' '.join(res)
    cls = client.classify(btext)
    # page = {'url': url, 'btext': btext}
    page = SPage(url=url, btext=btext)
    # log.msg(page['referer'], loglevel=log.CRITICAL)
    log.msg(page['url'], loglevel=log.CRITICAL)
    log.msg(cls, loglevel=log.CRITICAL)
    addtodb(page, parenturl, cls)
    return page


class SPage(Item):
    url = Field()
    btext = Field()
    referer = Field()


class FollowAllSpider(Spider):

    name = 'followall'

    def __init__(self, **kw):
        super(FollowAllSpider, self).__init__(**kw)
        url = kw.get('url') or kw.get('domain') or 'http://scrapinghub.com/'
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'http://%s/' % url
        self.url = url
        self.allowed_domains = [re.sub(r'^www\.', '', urlparse.urlparse(url).hostname)]
        self.link_extractor = LinkExtractor()
        self.cookies_seen = set()

    def start_requests(self):
        return [Request(self.url, callback=self.parse, dont_filter=True)]

    def parse(self, response):
        page = crawl_page(response.url, self.url)
        r = [page]
        if isinstance(response, HtmlResponse):
            links = self.link_extractor.extract_links(response)
            r.extend(Request(x.url, callback=self.parse) for x in links)
        return r


def stop_reactor():
    reactor.stop()


def crawl_address(url):
    dispatcher.connect(stop_reactor, signal=signals.spider_closed)
    spider = FollowAllSpider(domain=url)
    settings = get_project_settings()
    crawler = Crawler(settings)
    crawler.signals.connect(reactor.stop, signal=signals.spider_closed)
    crawler.configure()
    crawler.crawl(spider)
    crawler.start()
    log.start()
    log.msg('Running reactor...')
    reactor.run()
    log.msg('Reactor stopped.')


def newurl(url):
    env = open_env()
    urls = env.open_db('urls')
    with env.begin(db=urls, write=True) as txn:
        log.msg(url)
        t = url.encode('utf-8')
        tres = txn.get(t)
        print url
        print tres
        if tres:
            res = False
        else:
            res = True
    env.close()
    return res


def crawl(url):
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'http://%s/' % url
    import threading
    if newurl(url):
        print "New URL"
    else:
        print "URL already in DB"
        return
    print url
    # get correct title, detect language
    p = Site(title=url, url=url, show=0)
    p.published = datetime.datetime.today()
    p.save()

    thr = threading.Thread(target=crawl_address, args=[url], kwargs={})
    thr.start()
    return
