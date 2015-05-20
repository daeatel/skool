from skool.settings import CSTRING
from skool.models import Page
from skool.settings import *
from skool.utils import makepath
from sklearn.feature_extraction.text import TfidfTransformer, CountVectorizer
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.svm import LinearSVC
from sklearn.externals import joblib
import xmlrpclib
import pickle
import os
from sklearn.metrics import *

client = xmlrpclib.ServerProxy(CSTRING, allow_none=True)


def classify(text):
    '''
    Classify given text to educational subjects

    :param text: text to classify
    :type text: str
    :returns: ids of labels
    :rtype: array of ints
    '''
    return client.classify(text)


def classify_edu(text):
    '''
    Classify given text as education or non-educational content

    :param text: text to classify
    :type text: str
    :returns: 1 for non-educational content, 2 for educational content
    :rtype: array with one int
    '''
    return client.classify_edu(text)


def get_all_data():
    ''' Get data for educational subjects classifier'''
    print "Gathering data"
    data_train = []
    labels_train_normal = []
    for page in [x for x in Page.objects if x.cze]:
        data_train.append(page.cleannostops.encode('utf-8'))
        labs = [x.id for x in page.labels_all]
        labs = set(labs)
        labels_train_normal.append(labs)
    mlb = MultiLabelBinarizer()
    labels_train = mlb.fit_transform(labels_train_normal)
    print "Saving MLB"
    path = os.path.join(makepath('model'), DEFAULT_FILENAMES['MultiLabelBinarizer'] + '.pkl')
    joblib.dump(mlb, path)
    print "Saved"
    return (data_train, labels_train)


def train_model():
    ''' Train classification model for educational subjects'''
    (train_data, train_label) = get_all_data()
    print "Training from", len(train_data), "examples"

    print "Training CountVectorizer"
    cv = CountVectorizer()
    res = cv.fit_transform(train_data)
    print "Saving it"
    joblib.dump(cv, os.path.join(makepath('model'), DEFAULT_FILENAMES['CountVectorizer'] + '.pkl'))

    print "TfIdf transforming"
    tfidf = TfidfTransformer()
    ti = tfidf.fit_transform(res)
    print "Saving it"
    joblib.dump(tfidf, os.path.join(makepath('model'), DEFAULT_FILENAMES['TfIdf'] + '.pkl'))

    print "Training classifier"
    cls = OneVsRestClassifier(LinearSVC(), -1)
    cls.fit(ti, train_label)
    print "Saving it"
    joblib.dump(cls, os.path.join(makepath('model'), DEFAULT_FILENAMES['Classifier'] + '.pkl'))
    print "Done"
    test = cls.predict(ti)
    print classification_report(train_label, test)


def get_edu_data():
    ''' Get data for educational/non-educational classifier'''
    print "Gathering data"
    with open(makepath('noneduurl.pkl'), 'r') as fh:
        nonedu = pickle.load(fh)

    with open(makepath('eduurl.pkl'), 'r') as fh:
        edu = pickle.load(fh)

    data_train = []
    labels_train_normal = []
    for url in nonedu:
        page = Page.objects(url=url).first()
        data_train.append(page.cleannostops.encode('utf-8'))
        labels_train_normal.append('1')
    for url in edu:
        page = Page.objects(url=url).first()
        data_train.append(page.cleannostops.encode('utf-8'))
        labels_train_normal.append('2')

    return (data_train, labels_train_normal)


def train_edu_model():
    ''' Train classification model for educational/non-educational'''
    (train_data, train_label) = get_edu_data()
    print "Training from", len(train_data), "examples"

    print "Training CountVectorizer"
    cv = CountVectorizer()
    res = cv.fit_transform(train_data)
    print "Saving it"
    joblib.dump(cv, os.path.join(makepath('edumodel'), DEFAULT_FILENAMES['CountVectorizer'] + '.pkl'))

    print "TfIdf transforming"
    tfidf = TfidfTransformer()
    ti = tfidf.fit_transform(res)
    print "Saving it"
    joblib.dump(tfidf, os.path.join(makepath('edumodel'), DEFAULT_FILENAMES['TfIdf'] + '.pkl'))

    print "Training classifier"
    cls = LinearSVC()
    cls.fit(ti, train_label)
    print "Saving it"
    joblib.dump(cls, os.path.join(makepath('edumodel'), DEFAULT_FILENAMES['Classifier'] + '.pkl'))
    print "Done"
