from skool.settings import *
from subprocess import call
import requests
import shutil
import os


def makepath(append, basepath=BASEPATH):
    return os.path.abspath(os.path.join(basepath, append))


def dump_db(path=None, remove=True):
    if not path:
        path = makepath('dump')
    print "Dumping database to", path
    if remove and os.path.isdir(path):
        shutil.rmtree(path)
    args = ["mongodump", "--host", MONGODB_HOST + ":" + str(MONGODB_PORT), "--db", MONGODB_DB, "--out", path]
    if MONGODB_USER:
        args.append("--username")
        args.append(MONGODB_USER)
    if MONGODB_PASS:
        args.append("--password")
        args.append(MONGODB_PASS)
    call(args)


def restore_db(path=None, remove=False):
    if not path:
        path = makepath('dump')
    print "Restoring database from", path
    args = ["mongorestore", "--host", MONGODB_HOST + ":" + str(MONGODB_PORT)]
    if MONGODB_USER:
        args.append("--username")
        args.append(MONGODB_USER)
    if MONGODB_PASS:
        args.append("--password")
        args.append(MONGODB_PASS)
    if remove:
        args.append("--drop")
    args.append(path)
    call(args)


# = init_search_index()
def init_mongodb_river():
    body = '''{
        "type": "mongodb",
        "mongodb": {
            "servers": [
                {"host": "%s", "port": %d}
            ],
            "db": "%s",
            "collection": "%s",
            "options": {"secondary_read_preference": true}
        },
        "index": {
            "name": "%s",
            "type": "%s"
        }
    }''' % (MONGODB_HOST, MONGODB_PORT, MONGODB_DB, MONGODB_COLLECTION, INDEX_NAME, INDEX_TYPE)
    r = requests.put('http://localhost:9200/_river/skool/_meta/', data=body)
    print r.status_code
    print r.content


# Check that your index is in Elasticsearch

# curl -XGET http://localhost:9200/_aliases
# Check your cluster health.

# curl -XGET 'http://localhost:9200/_cluster/health?pretty=true'
# It's probably yellow with some unassigned shards. We have to tell Elasticsearch what we want to work with.

# curl -XPUT 'localhost:9200/_settings' -d '{ "index" : { "number_of_replicas" : 0 } }'
# Check cluster health again. It should be green now.

# curl -XGET 'http://localhost:9200/_cluster/health?pretty=true'
