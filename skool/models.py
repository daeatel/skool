#!/usr/bin/python
# encoding=utf-8
import blinker  # import is not needed, but it has to be installed in order to use signals
from skool.difficulty import mistrik
from skool.utils import makepath
from mongoengine import *
from mongoengine import signals
import distance
import operator
import sys
connect('skool')


def get_stopwords():
    with open(makepath('stopwords/czech.txt'), 'r') as fh:
        data = set([word.strip().decode('utf-8') for word in fh.readlines()])
    return list(data)


class Label(Document):
    id = SequenceField(required=True, unique=True, primary_key=True)
    name = StringField(required=True, unique=True)
    valid = BooleanField(required=True, default=True)
    label = BooleanField()

    @classmethod
    def filter_labels(cls, threshold=100):
        print "Gathering labels frequencies"
        labelfreq = {}
        for label in Label.objects:
            labelfreq[label.id] = 0
        for page in Page.objects:
            sys.stdout.write('.')
            sys.stdout.flush()
            for l in page.labels_all:
                labelfreq[l.id] += 1
        print "Filtering labels"
        sd = sorted(labelfreq.items(), key=operator.itemgetter(1))
        res = []
        for key, val in sd:
            sys.stdout.write('.')
            sys.stdout.flush()
            l = Label.objects(id=key).first()
            if val >= threshold:
                res.append((l.name, key, val))
                l.valid = True
            else:
                l.valid = False
            l.save()
        # 333, min 1 = 232
        # 333, min 25 = 162
        # 333, min 100 = 94
        # 150 = 71
        # 200 = 56
        # 250 = 47
        print "Done", len(res), "labels are OK"


class Category(Document):

    '''
    >>> _ = Category.objects(name="Skákal pes » Oves » Zelenou louku").delete()
    >>> c = Category(name="Skákal pes » Oves » Zelenou louku")
    >>> _ = c.save()
    >>> [l.name for l in c.labels]
    [u'sk\\xe1kal pes', u'oves', u'zelenou louku']
    >>> Category.objects(name="Skákal pes » Oves » Zelenou louku").delete()
    1
    '''
    name = StringField(required=True, unique=True)
    labels = ListField(ReferenceField(Label))

    @classmethod
    def categories_to_labels(cls, sender, document):
        if not document.labels:
            add = []
            labs = [x.strip().lower() for x in document.name.split(u"»")]
            for lab in labs:
                res = Label.objects(name=lab).first()
                if not res:
                    res = Label(name=lab)
                    res.save()
                add.append(res)
            document.labels = add

signals.pre_save.connect(Category.categories_to_labels, sender=Category)


class Language(Document):
    id = IntField(required=True, unique=True, primary_key=True)
    name = StringField(required=True, unique=True)


class Keyword(Document):
    name = StringField(required=True, unique=True)


class Page(Document):

    '''Single web page

    >>> _ = Page.objects(url="http://www.example.com/").delete()
    >>> _ = Site.objects(url="http://www.example.com/").delete()
    >>> cze = Language.objects(name='Čeština').first()
    >>> p = Site(url="http://www.example.com/", language=cze)
    >>> _ = p.save()
    >>> c = Page(url="http://www.example.com/", btext="Skákal pes přes oves. Přes zelenou louku.", parent=p)
    >>> _ = c.save()
    >>> c.cze
    True
    >>> c.diff
    44
    >>> c.cleanbtext
    u'sk\\xe1kal pes p\u0159es oves p\u0159es zelenou louku'
    >>> c.cleannostops
    u'sk\\xe1kal pes oves zelenou louku'
    >>> Page.objects(url="http://www.example.com/").delete()
    1
    >>> Site.objects(url="http://www.example.com/").delete()
    1
    '''
    btext = StringField()
    cleanbtext = StringField()
    cleannostops = StringField()
    url = URLField(required=True)
    label_teacher = ListField(ReferenceField(Category))
    label_model = ListField(ReferenceField(Label))
    diff = FloatField()
    # v uvozovkach kvuli circular reference
    parent = ReferenceField('Site')
    recs = ListField(ReferenceField('Page'))
    # introduce State variable, instead of all these?
    directory = BooleanField(required=True, default=False)
    classified = BooleanField(required=True, default=False)
    deleted = BooleanField(required=True, default=False)
    labeled = BooleanField(required=True, default=False)
    educational = BooleanField(required=True, default=False)

    @property
    def labels_teacher(self):
        return [x for cat in self.label_teacher for x in cat.labels]

    @property
    def labels_all(self):
        return [x for cat in self.parent.categories for x in cat.labels if x.valid]

    @property
    def cze(self):
        if self.parent and self.parent.language:
            return self.parent.language.name == u"Čeština"
        else:
            return False

    @property
    def keywords(self):
        return self.parent.keywords

    class Meta:  # try to delete this
        app_label = 'skool'

    @classmethod
    def compute_diff(cls, sender, document):
        if document.cze and not document.diff:
            document.diff = mistrik(document.btext)

    @classmethod
    def clean_btexts(cls, document):
        if document.cze and document.btext and not document.cleannostops:
            chars = ',;:.\'"!?$\\/-()[]{}=*+|'
            trans = dict.fromkeys(map(ord, chars), u' ')
            btext = document.btext
            btext = btext.translate(trans)
            btext = btext.lower()
            btext = ' '.join(btext.split())
            document.cleanbtext = btext
            stops = get_stopwords()
            document.cleannostops = ' '.join([x for x in document.cleanbtext.split() if x not in stops])

    @classmethod
    def predict_labels(cls, document):
        if document.cleannostops and not document.label_model:
            from skool.classify import classify
            res = classify(document.cleannostops)
            add = []
            for r in res:
                l = Label.objects(id=r).first()
                if l:
                    add.append(l)
            document.label_model = add

    @classmethod
    def update_page_recs(cls, document):
        res = {}
        for site in Page.objects():
            if site != document:
                kwa, kwb = document.label_model, site.label_model
                ca = set(kwa)
                cb = set(kwb)
                if len(ca) > 0 and len(cb) > 0:
                    res[site.id] = distance.sorensen(ca, cb)
                else:
                    res[site.id] = 1  # 1 = totally different
        best = sorted(res.iteritems(), key=operator.itemgetter(1), reverse=False)[:10]
        ret = []
        for (obj, score) in best:
            s = Page.objects(id=obj).first()
            ret.append(s)
        document.recs = ret
        document.save()

    @classmethod
    def compute_recs(cls, document):
        if not document.parent and not document.recs:
            Page.update_page_recs(document)

    @classmethod
    def pre_save_seq(cls, sender, document):
        cls.clean_btexts(document)
        cls.predict_labels(document)
        cls.compute_recs(document)

signals.pre_save.connect(Page.compute_diff, sender=Page)
signals.pre_save.connect(Page.pre_save_seq, sender=Page)


class Site(Document):

    '''
    >>> _ = Keyword.objects(name="example1").delete()
    >>> _ = Keyword.objects(name="example2").delete()
    >>> _ = Keyword.objects(name="example3").delete()
    >>> k1 = Keyword(name="example1")
    >>> _ = k1.save()
    >>> k2 = Keyword(name="example2")
    >>> _ = k2.save()
    >>> k3 = Keyword(name="example3")
    >>> _ = k3.save()
    >>> _ = Site.objects(url="http://www.example.com/").delete()
    >>> _ = Site.objects(url="http://www.exexample.com/").delete()
    >>> a = Site(url="http://www.example.com/", keywords=[k1, k2])
    >>> _ = a.save()
    >>> b = Site(url="http://www.exexample.com/", keywords=[k2, k3])
    >>> _ = b.save()
    >>> b.recs[0].url
    u'http://www.example.com/'
    >>> Site.compute_recs(Site, a)
    >>> a.recs[0].url
    u'http://www.exexample.com/'
    >>> Site.objects(url="http://www.example.com/").delete()
    1
    >>> Site.objects(url="http://www.exexample.com/").delete()
    1
    >>> Keyword.objects(name="example1").delete()
    1
    >>> Keyword.objects(name="example2").delete()
    1
    >>> Keyword.objects(name="example3").delete()
    1
    '''
    url = URLField(required=True, unique=True)
    title = StringField()
    description = StringField()
    description2 = StringField()
    author = StringField()
    rating_rvp = DecimalField(min_value=0, max_value=5)
    rating_users = DecimalField(min_value=0, max_value=5)
    published = DateTimeField()
    show = IntField(min_value=0)
    image_url = URLField()
    recs = ListField(ReferenceField('Site'))
    children_labeled = ListField(ReferenceField(Page))
    categories = ListField(ReferenceField(Category))
    keywords = ListField(ReferenceField(Keyword))
    children = ListField(ReferenceField(Page))
    language = ReferenceField(Language)

    @classmethod
    def update_site_recs(cls, document):
        res = {}
        for site in Site.objects():
            if site != document:
                kwa, kwb = document.keywords, site.keywords
                ca = set(kwa)
                cb = set(kwb)
                if len(ca) > 0 and len(cb) > 0:
                    res[site.id] = distance.sorensen(ca, cb)
                else:
                    res[site.id] = 1  # 1 = totally different
        best = sorted(res.iteritems(), key=operator.itemgetter(1), reverse=False)[:10]
        ret = []
        for (obj, score) in best:
            s = Site.objects(id=obj).first()
            ret.append(s)
        document.recs = ret
        document.save()

    @classmethod
    def update_all_recs(cls):
        print "Rebuilding all Site's recommendations"
        for site in Site.objects():
            Site.update_site_recs(site)
            sys.stdout.write('.')
            sys.stdout.flush()


if __name__ == '__main__':
    import doctest
    # doctest.ELLIPSIS_MARKER = '-etc-'
    # doctest.testmod(optionflags=doctest.ELLIPSIS)
    # or just assign result to dummy _
    doctest.testmod()
