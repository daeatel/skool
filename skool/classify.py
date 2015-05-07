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
import os


def classify(text):
    client = xmlrpclib.ServerProxy(CSTRING, allow_none=True)
    return client.classify(text)


def get_all_data():
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
