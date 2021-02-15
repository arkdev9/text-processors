import time

from elasticsearch import Elasticsearch
from ..config import DB_HOST, DB_PORT, DB_USER, DB_PW, ES_CONN_SCHEME

es = Elasticsearch(["{}://{}:{}".format(ES_CONN_SCHEME, DB_HOST, DB_PORT)],
                   http_auth=(DB_USER, DB_PW), verify_certs=False)


def check_create_index(index):
    exists = es.indices.exists(index)
    if exists:
        return True
    else:
        mapping = {
            "mappings": {
                "properties": {
                    "team_id": {"type": "keyword"},
                    "channel_id": {"type": "keyword"},
                    "user": {"type": "keyword"},
                    "full_doc": {"type": "boolean"},
                    "is_file": {"type": "boolean"},
                    "url": {"type": "text"},
                    "name": {"type": "keyword"},
                    "text": {"type": "text"},
                    "posted_date": {"type": "double"},
                    "latest_ts": {"type": "double"},
                }
            }
        }
        es.indices.create(index=index, body=mapping)


def put_dicts_webextension(file_name, user):
    i = 1
    doc_count = 0
    text = []
    indextostore = "webextension"
    for sentence in sents:
        sent = str(sentence).strip()
        if i % 40 == 0:
            text_to_put = ' '.join(text)
            pack = {
                'text': text_to_put,
                'text_len': len(text_to_put),
                'name': file_name,
                'user': user,
            }
            res = es.index(index=indextostore, body=pack)
            text = [sent]
            doc_count += 1
            i = 1
            continue
        text.append(sent)
        i += 1

    text_to_put = ' '.join(text)
    res = es.index(index=indextostore, body={
        'text': text_to_put,
        'text_len': len(text_to_put),
        'name': file_name,
        'user': user,
    })

    return doc_count


def put_dicts(text, file_name, teamid, channelid, url, indextostore):
    res = es.index(index=indextostore, body={
        'text': text,
        'name': file_name,
        'team_id': teamid,
        'channel_id': channelid,
        'full_doc': True,
        'is_file': True,
        'latest_ts': time.time(),
        'url': url
    })
