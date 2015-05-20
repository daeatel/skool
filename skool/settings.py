# path to folder with data
BASEPATH = '/home/michal/Develop/oshiftdata/'
# name of the Elasticsearch index
INDEX_NAME = 'pagesbtext'
# type of the Elasticsearch index
INDEX_TYPE = 'page'
# host address of MongoDB
MONGODB_HOST = "127.0.1.1"
# port of MongoDB
MONGODB_PORT = 27017
# name of MongoDB database
MONGODB_DB = "skool"
# name of collection, where bodytexts are saved
MONGODB_COLLECTION = "page"
# username for accessing database
MONGODB_USER = None
# password for accessing database
MONGODB_PASS = None

# ELASTIC_HOST
# ELASTIC_PORT

# url on which classification server will listen
URL = "localhost"
# port on which classification server will listen
PORT = 8001
# connection string to classification server
CSTRING = "http://localhost:8001"
# filenames of files with serialized model
DEFAULT_FILENAMES = {
    'CountVectorizer': 'cv',
    'TfIdf': 'tfidf',
    'Classifier': 'cls',
    'MultiLabelBinarizer': 'mlb'
}
