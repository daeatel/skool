#!/usr/bin/python
# encoding=utf-8
import datetime
import urlparse
import re
import lmdb
import pytz
import iso8601
import justext
import xmlrpclib
import urllib2
import threading
from BeautifulSoup import BeautifulSoup

from models import Page, Site, Label

DB_PATH = '/tmp/dbtest'
now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)


def __open_env():
    ''' Open LMDB instance'''
    return lmdb.open(DB_PATH, max_dbs=1)


def rebuild_url_lookup():
    ''' Rebuld URL lookup data'''
    print "Rebuilding URL"
    env = __open_env()
    urls = env.open_db('urls')
    with env.begin(db=urls, write=True) as txn:
        cursor = txn.cursor()
        for k, v in cursor:
            txn.delete(k)
        for item in Page.objects():
            t = item.url.encode('utf-8')
            txn.put(t, '1')
    print "Done"
    env.close()


env = __open_env()

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
    '''
    Add URL to URL lookup

    :param url: URL to add
    :type url: str
    '''
    env = __open_env()
    urls = env.open_db('urls')
    with env.begin(db=urls, write=True) as txn:
        txn.put(url.encode('utf-8'), '1')
    env.close()


def addtodb(page, lookupurl, classes):
    '''
    Add page to MongoDB

    :param page: info about page
    :type page: dict
    :param lookupurl: URL of parent site
    :type lookupurl: str
    :param classes: result of classification for given page
    :type classes: array of ints
    '''
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
    '''
    Crawl single page and add it to db

    :param url: URL of webpage to be crawled
    :type url: str
    :param parenturl: URL of parent website, obtained automatically if ommited
    :type parenturl: str
    '''
    if not newurl(url):
        return
    # if not parenturl:
    #     parsed = urlparse.urlparse(url)
    #     parenturl = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed)
    res = []
    urls = []
    try:
        response = urllib2.urlopen(url)
    except Exception:
        return urls
    if response.info().maintype == 'text':
        print url
        body = response.read()
        response.close()
        soup = BeautifulSoup(body)

        for tag in soup.findAll('a', href=True):
            tag['href'] = urlparse.urljoin(url, tag['href'])
            urls.append(tag['href'])

        if not body:
            return urls
        paragraphs = justext.justext(body, justext.get_stoplist("Czech"))
        for para in paragraphs:
            if not para.is_boilerplate:
                res.append(para.text)
        btext = ' '.join(res)
        isedu = client.classify_edu(btext)[0]
        page = {'url': url, 'btext': btext}
        print isedu
        if isedu == 2:  # is educational
            cls = client.classify(btext)
            addtodb(page, parenturl, cls)
    return urls


def __crawl_address(site):
    '''
    Crawl entire site

    :param url: URL of website
    :type url: str
    '''
    print site
    urls_queue = [site]
    urls_found = []
    urls_done = []
    domain = ''

    mre = re.match('^https?://[^/]*', site, re.IGNORECASE)
    if mre:
        domain = mre.group(0)

    while len(urls_queue) > 0:

        url = urls_queue.pop()
        urls_done.append(url)

        found = crawl_page(url)

        for uf in found:
            if not uf.startswith(domain):
                continue

            if uf not in urls_found:
                urls_found.append(uf)

            if uf not in urls_queue and uf not in urls_done:
                urls_queue.append(uf)

        print "Done %d; Queued %d; Found %d" % (len(urls_done), len(urls_queue), len(urls_found))


def newurl(url):
    '''
    Is URL new? (ie. not in lookup)

    :param url: URL to check
    :type url: str
    :returns: is URL new?
    :rtype: bool
    '''
    env = __open_env()
    urls = env.open_db('urls')
    with env.begin(db=urls, write=True) as txn:
        t = url.encode('utf-8')
        tres = txn.get(t)
        if tres:
            res = False
        else:
            res = True
    env.close()
    print res
    return res


def crawl(url):
    '''
    Crawl entire site

    :param url: URL of website
    :type url: str
    '''
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'http://%s/' % url
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

    thr = threading.Thread(target=__crawl_address, args=[url], kwargs={})
    thr.start()
    return
