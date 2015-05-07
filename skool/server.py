#!/usr/bin/python
# encoding=utf-8
from sklearn.externals import joblib
from SimpleXMLRPCServer import SimpleXMLRPCServer
from settings import URL, PORT, DEFAULT_FILENAMES


def start(path, url=URL, port=PORT, user_filenames=None):
    filenames = DEFAULT_FILENAMES
    if user_filenames:
        filenames.update(user_filenames)
    if not path.endswith('/'):
        path += '/'

    print "Loading model from " + path
    cv = joblib.load(path + filenames['CountVectorizer'] + '.pkl')
    tfidf = joblib.load(path + filenames['TfIdf'] + '.pkl')
    cls = joblib.load(path + filenames['Classifier'] + '.pkl')
    mlb = joblib.load(path + filenames['MultiLabelBinarizer'] + '.pkl')

    def classify(text):
        a = cv.transform([text])
        b = tfidf.transform(a)
        c = cls.predict(b)
        res = mlb.inverse_transform(c)
        # for i in res[0]:
        #    ans.append(str(Label.objects(id=i).first().id))
        res = map(int, res[0])
        return res

    server = SimpleXMLRPCServer((URL, PORT))
    server.register_introspection_functions()
    server.register_function(classify)

    print "Server is ready! Exit by CTRL+C"
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    from skool.utils import makepath
    start(makepath('model'))
