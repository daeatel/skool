from datetime import datetime
from skool.utils import makepath
from skool.models import *
import subprocess
import pickle
import json
import sys
import re
import os


def get_rvp_categories():
    ''' Start scrapy crawler which obtains tree of categories from http://odkazy.rvp.cz/'''
    p = subprocess.Popen(['scrapy', 'crawl', 'cats'], cwd=os.path.join(os.path.dirname(__file__), './scrapy/cats'))
    p.wait()


def get_rvp_pages():
    ''' Start scrapy crawler which obtains tree of categories from http://odkazy.rvp.cz/'''
    p = subprocess.Popen(['scrapy', 'crawl', 'rvps'], cwd=os.path.join(os.path.dirname(__file__), './scrapy/pages'))
    p.wait()


def __parse_date(s):
    '''
    Convert date from format 21. 04. 2015 to datetime format

    :param s: date string to parse
    :type s: str
    :returns: datetime representation of input string
    :rtype: datetime
    '''
    match = re.search(r'(\d+)\.\s(\d+)\.\s(\d+)', s)
    md = int(match.group(1))
    mm = int(match.group(2))
    my = int(match.group(3))
    return datetime(my, mm, md, 12, 0)


def __sites_to_mongo(sites_path, langs_path):
    '''
    Import data about RVP sites into MongoDB

    :param sites_path: path to file with info about sites
    :type sites_path: str
    :param langs_path: path to file with info about languages
    :type langs_path: str
    '''
    json_obj = open(sites_path)
    data = json.load(json_obj)
    json_obj.close()

    langs_obj = open(langs_path)
    langs = json.load(langs_obj)
    langs_obj.close()

    print "Importing", len(data), "sites from", sites_path, "and", len(langs), "languages from", langs_path

    for key, value in langs.iteritems():
        lang = Language(id=value, name=key)
        lang.save()

    lookup = set()
    lookup.add("root")

    cnt = 0
    ctc = 0
    added = []

    for page in data:
        page['url'] = page['url'].strip()
        if page['url'][0] == 'w':
            page['url'] = 'http://' + page['url']
        if page['url'] in lookup:
            sys.stdout.write('-')
            sys.stdout.flush()
            cnt += 1
        else:
            sys.stdout.write('.')
            sys.stdout.flush()
            lang = Language.objects(id=page['lang']).first()

            p = Site(title=page['name'], author=page['author'], url=page['url'], language=lang, show=page['show'])

            p.published = __parse_date(page['published'])
            p.image_url = page['image_urls'][0]
            p.rating_rvp = page.get('rating_rvp')
            p.rating_users = page.get('rating_users')
            p.description = page.get('description')
            p.description2 = page.get('description2')

            for cat in page['categories']:
                cat = cat[4:-5].replace('...', '')
                res = Category.objects(name=cat).first()
                if not res:
                    res = Category(name=cat)
                    res.save()
                    ctc += 1
                p.categories.append(res)

            for kword in page['keywords']:
                res = Keyword.objects(name=kword).first()
                if not res:
                    res = Keyword(name=kword)
                    res.save()
                p.keywords.append(res.to_dbref())
            p.save()
            added.append(str(res) + '\n')
            lookup.add(p.url)
    print "Importing finished.", cnt, "duplicates detected.", ctc, "categories added."


def import_sites():
    ''' Import RVP data into MongoDB (old data are deleted)'''
    Keyword.objects.delete()
    Language.objects.delete()
    Label.objects.delete()
    Category.objects.delete()
    Site.objects.delete()
    Page.objects.delete()
    sites_path = makepath('data/sites.json')
    langs_path = makepath('data/langs.json')
    __sites_to_mongo(sites_path, langs_path)
    Site.update_all_recs()


def __create_btext_lookup():
    ''' Create file for looking up page's parent site '''
    print "Creating lookup for bodytexts"
    pages = [x.url.strip() for x in Site.objects]

    lookup = {}
    for file in os.listdir(makepath("linktrees")):
        if file.endswith(".pkl"):
            filename = 'linktrees/' + file
            with open(makepath(filename)) as fh:
                data = pickle.load(fh)
            if data:
                for base, item in data.iteritems():
                    if base.strip() in pages:
                        sys.stdout.write('.')
                        sys.stdout.flush()
                        for i in item:
                            lookup[i.strip()] = base.strip()

    with open(makepath('data/lookup.pkl'), 'w') as fh:
        pickle.dump(lookup, fh)


def __load_btexts():
    ''' Load gathered bodytexts and import them to MongoDB with appropriate site reference'''
    print "Inserting bodytexts"
    with open(makepath('data/lookup.pkl'), 'r') as fh:
        lookup = pickle.load(fh)

    Page.objects.delete()
    for s in Site.objects:
        s.children = []
        s.save()
    # pagesurls = [x.url.strip() for x in Site.objects]

    for file in os.listdir(makepath('bodytexts')):
        filepath = 'bodytexts/' + file
        with open(makepath(filepath), 'r') as fh:
            burl, btext = fh.readlines()
        burl = burl.strip()
        try:
            base = lookup[burl]
        except KeyError:
            sys.stdout.write('x')
            continue
        site = Site.objects(url=base).first()
        if site:
            sys.stdout.write('.')
            sys.stdout.flush()
            nov = Page(url=burl, btext=btext, parent=site)
            nov.save()
            site.children.append(nov)
            site.save()


def import_pages():
    ''' Import data about individual pages to MongoDB'''
    __create_btext_lookup()
    __load_btexts()
    Label.filter_labels()


def clear_labels():
    ''' Set all labels of all pages to False or empty'''
    for site in Site.objects:
        site.children_labeled = []
        site.save()

    for page in Page.objects:
        page.dir = False
        page.label_teacher = []
        page.deleted = False
        page.labeled = False
        page.save()
