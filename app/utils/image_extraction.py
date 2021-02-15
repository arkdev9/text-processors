from base64 import b64decode
import os
import os.path
from os import path
import requests
import tempfile
import jwt
import json
from werkzeug.utils import secure_filename
from google.cloud import storage
from datetime import datetime
from elasticsearch import Elasticsearch
import re
import pytesseract

from .text_processor import clean_text

es = Elasticsearch(["https://35.230.52.64:9200"],
                   http_auth=("elastic", "IyuPrspNGoG6a5gHBa3C"), verify_certs=False)


def get_file_path(filename):
    file_name = secure_filename(filename)
    return os.path.join(tempfile.gettempdir(), file_name)


def upload_blob(bucket_name, source_file_name, destination_blob_name, user, data):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    doc = {
        "user": user,
        "object_id": blob._properties['id'],
        "media_link": blob._properties['mediaLink'],
        "text": data
    }
    es.index(index="webextension-images", body=doc)


def image_extractor(auth, data_uri):
    pytesseract.pytesseract.tesseract_cmd = r'tesseract'
    user = ''
    try:
        print('try', auth)
        res = requests.get('http://35.230.52.64:42069/jwt_secrets')
        res = json.loads(res.content)
        print('res: {}'.format(res))
        secret = res[0]['secret']
        payload = jwt.decode(
            auth, 'c046e87565f655ba77e8be6bfde9ab0fbff3b0f21c02fd20d6b79f4fec92d111', algorithms=["HS256"])
        user = payload["email"]
    except Exception as e:
        print('30', str(e))
        return ("Not authorized", 403)
    try:
        print('over here')
        header, encoded = data_uri.split(",", 1)
        data = b64decode(encoded)
        time_stamp = datetime.now()
        file_name = user + str(time_stamp) + '.png'
        path_name = get_file_path(file_name)
        with open(path_name, "wb") as f:
            f.write(data)
        img = path_name
        data = pytesseract.image_to_string(
            img, lang='eng', config=" -c preserve_interword_spaces=1 --oem 3 --psm 11 ")
        data = re.sub(
            '[^a-zA-Z0-9\n/ !"#$%&=~()*+,./:;<>?@[\]^_-`{|}]', '', data)
        data = clean_text(data)
        print('Data: {}'.format(data))
        upload_blob("webextension-images", path_name,
                    user+'_'+str(time_stamp), user, data)
        os.remove(path_name)
        return ("Success", 200)
    except Exception as e:
        print(str(e))
        return ("Error", 500)
