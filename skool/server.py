#!/usr/bin/python
# encoding=utf-8
from sklearn.externals import joblib
from SimpleXMLRPCServer import SimpleXMLRPCServer
from settings import URL, PORT, DEFAULT_FILENAMES
from skool.utils import makepath


def start(url=URL, port=PORT, user_filenames=None):
    '''
    Start classification server

    :param url: on which address server will listen, default from settings
    :type url: str
    :param port: port on which the server will listen
    :type port: int
    :param user_filenames: override default filenames of serialized model, default from settings
    :type user_filenames: dict
    '''
    filenames = DEFAULT_FILENAMES
    if user_filenames:
        filenames.update(user_filenames)

    path = makepath('model') + '/'
    print "Loading model from " + path
    cv = joblib.load(path + filenames['CountVectorizer'] + '.pkl')
    tfidf = joblib.load(path + filenames['TfIdf'] + '.pkl')
    cls = joblib.load(path + filenames['Classifier'] + '.pkl')
    mlb = joblib.load(path + filenames['MultiLabelBinarizer'] + '.pkl')

    path = makepath('edumodel') + '/'
    print "Loading edu model from " + path
    edu_cv = joblib.load(path + filenames['CountVectorizer'] + '.pkl')
    edu_tfidf = joblib.load(path + filenames['TfIdf'] + '.pkl')
    edu_cls = joblib.load(path + filenames['Classifier'] + '.pkl')

    def classify(text):
        '''
        Classify given text to educational subjects

        :param text: text to classify
        :type text: str
        :returns: ids of labels
        :rtype: array of ints
        '''
        a = cv.transform([text])
        b = tfidf.transform(a)
        c = cls.predict(b)
        res = mlb.inverse_transform(c)
        # for i in res[0]:
        #    ans.append(str(Label.objects(id=i).first().id))
        res = map(int, res[0])
        return res

    def classify_edu(text):
        '''
        Classify given text as education or non-educational content

        :param text: text to classify
        :type text: str
        :returns: 1 for non-educational content, 2 for educational content
        :rtype: array with one int
        '''
        a = edu_cv.transform([text])
        b = edu_tfidf.transform(a)
        res = edu_cls.predict(b)
        res = map(int, res[0])
        return res  # 1=nonedu, 2=edu

    server = SimpleXMLRPCServer((URL, PORT))
    server.register_introspection_functions()
    server.register_function(classify)
    server.register_function(classify_edu)

    print "Server is ready! Exit by CTRL+C"
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
