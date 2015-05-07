from elasticsearch import Elasticsearch
from models import Page
from settings import *
import re


def search(query, field, start=0, size=10, recommend=False, fuzzy=False, highlight=None):
    body = {
        "from": start,
        'query': {}
    }
    if size > 0:
        body['size'] = size
    query = re.sub(r'[/:]', '\\/', query)
    body['query']['query_string'] = {"fields": [field], "query": query, "default_operator": "AND"}
    if fuzzy:
        body['query']['query_string']['fuzziness'] = 'AUTO'  # is default - can be ommited
    else:
        body['query']['query_string']['fuzziness'] = 0  # or 1 - both should be ok
    if highlight and len(highlight) is 2:
        body['highlight'] = {
            "pre_tags": [highlight[0]],
            "post_tags": [highlight[1]],
            "fields": {
                field: {}
            }
        }
    # print body
    res = Elasticsearch().search(index=INDEX_NAME, body=body)
    # print res
    pres = []
    for r in res['hits']['hits']:
        hit = Page.objects(id=r['_source']['_id']).first()
        if highlight and len(highlight) is 2:
            hit.btext = '<br><br>'.join(r['highlight']['btext'])
        pres.append(hit)

    fin = []
    for page in pres:
        tmp = []
        if recommend:
            if page.parent:
                for r in page.parent.recs:
                    x = [r.url, r.title]
                    tmp.append(x)
            else:
                for r in page.recs:
                    x = [r.url, r.url]
                    tmp.append(x)
        fin.append([page, tmp])
    return (res['hits']['total'], fin)
