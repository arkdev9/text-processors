import logging
import os
import re
import json
import jwt
import shutil
import uuid
import requests
import textract

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Header
from datetime import datetime
from cleantext import clean
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, List, List, Dict

from haystack.preprocessor.preprocessor import PreProcessor
from haystack.document_store.elasticsearch import ElasticsearchDocumentStore
from haystack.file_converter.pdf import PDFToTextConverter
from haystack.file_converter.txt import TextConverter

from ..config import *

from ..utils.file_downloaders import download_file, download_webextension_file
from ..utils.text_processor import get_text_from_file,  get_file_path
from ..utils.scrape_utils import put_dicts, put_dicts_webextension, check_create_index
from ..utils.image_extraction import image_extractor

logger = logging.getLogger(__name__)
router = APIRouter()


document_store_webextension = ElasticsearchDocumentStore(
    host=DB_HOST,
    port=DB_PORT,
    username=DB_USER,
    password=DB_PW,
    index="webextension",
    scheme=ES_CONN_SCHEME,
    ca_certs=False,
    verify_certs=False,
    text_field=TEXT_FIELD_NAME,
    search_fields=SEARCH_FIELD_NAME,
    embedding_dim=EMBEDDING_DIM,
    embedding_field=EMBEDDING_FIELD_NAME,
    faq_question_field=FAQ_QUESTION_FIELD_NAME,
)


class DocsModel(BaseModel):
    url: str
    user: Optional[str]
    access_token: Optional[str]
    team_id: Optional[str]
    index: Optional[str]
    channel_id: Optional[str]
    gauth_access_token: Optional[str]


class WebextensionDocsModel(BaseModel):
    url: str
    platform: str


class WebextensionFilesModel(BaseModel):
    user: str


class ConversationTextModel(BaseModel):
    text: str


class ScrapeImageModel(BaseModel):
    data_uri: str


processor = PreProcessor(clean_empty_lines=True,
                         clean_whitespace=True,
                         clean_header_footer=True,
                         split_by="word",
                         split_length=200,
                         split_respect_sentence_boundary=True)


@router.post("/process-text")
def clean_text(request: ConversationTextModel):
    return processor.process({'text': request.text})


@router.post("/scrape-docs")
def scrape_docs(request: DocsModel):
    print(request)
    teamid = request.team_id
    channelid = request.channel_id
    url = request.url
    if request.user:
        user = request.user
    else:
        user = False
    print('-------->', url, user)
    response = {}

    ext, loc_path = download_file(url, user, request.access_token)
    text = get_text_from_file(ext, loc_path)
    name = loc_path.split('/')[-1].split('.')[0]
    processed_text = processor.process({'text': text})

    i = 0
    indextostore = request.index if request.index else 'staging'
    check_create_index(indextostore)
    for doc in processed_text:
        print(doc)
        doc_count = put_dicts(doc['text'], name, teamid,
                              channelid, url, request.index)
        response['doc_' + str(i)] = 'ok'
        i += 1

    if os.path.exists(loc_path):
        os.remove(loc_path)

    return response


@router.post("/scrape-website")
async def scrape_webextension_files(user: str = Form(...), file: UploadFile = File(...)):
    print(user)
    print(file, type(file))
    name = file.filename
    ext = name[name.rindex('.')+1:]
    print(name, ext)
    contents = await file.read()
    loc_path = get_file_path(file.filename)
    print(loc_path)
    with open(loc_path, 'wb') as f:
        f.write(contents)

    response = {}
    text = get_text_from_file(ext, loc_path)
    name = loc_path.split('/')[-1].split('.')[0]
    texts = processor.process({'text': text})

    for i in range(len(texts)):
        texts[i]["meta"]["user"] = user
        texts[i]["meta"]["name"] = name

    document_store_webextension.write_documents(texts)

    if os.path.exists(loc_path):
        os.remove(loc_path)

    return {"status": "ok"}

    ext, loc_path = download_file(url, user, request.access_token)
    text = get_text_from_file(ext, loc_path)
    name = loc_path.split('/')[-1].split('.')[0]
    processed_text = processor.process({'text': text})

    i = 0
    for doc in processed_text:
        print(doc)
        doc_count = put_dicts(doc['text'], name, teamid,
                              channelid, url, 'webextension')
        response['doc_' + str(i)] = 'ok'
        i += 1

    if os.path.exists(loc_path):
        os.remove(loc_path)

    return response


@router.post("/scrape-webextension-files")
async def scrape_webextension_files(file: UploadFile = File(...), authorization: Optional[str] = Header(None), ):
    email = ''
    try:
        print('try')
        res = requests.get('{}/jwt_secrets?'.format(PG))
        res = json.loads(res.content)
        secret = res[0]['secret']
        print(secret)
        payload = jwt.decode(authorization, secret, algorithms=["HS256"])
        email = payload["email"]
        print(email)
    except Exception as e:
        print(e)
        return 'Not authorized'
    print(file, type(file))
    name = file.filename
    ext = name[name.rindex('.')+1:]
    print(name, ext)
    contents = await file.read()
    loc_path = get_file_path(file.filename)
    print(loc_path)
    with open(loc_path, 'wb') as f:
        f.write(contents)

    response = {}
    text = get_text_from_file(ext, loc_path)
    name = loc_path.split('/')[-1].split('.')[0]
    texts = processor.process({'text': text})

    for i in range(len(texts)):
        texts[i]["meta"]["user"] = email
        texts[i]["meta"]["name"] = name

    document_store_webextension.write_documents(texts)

    if os.path.exists(loc_path):
        os.remove(loc_path)

    return {"status": "ok"}

    ext, loc_path = download_file(url, user, request.access_token)
    text = get_text_from_file(ext, loc_path)
    name = loc_path.split('/')[-1].split('.')[0]
    processed_text = processor.process({'text': text})

    i = 0
    for doc in processed_text:
        print(doc)
        doc_count = put_dicts(doc['text'], name, teamid, channelid, url)
        response['doc_' + str(i)] = 'ok'
        i += 1

    if os.path.exists(loc_path):
        os.remove(loc_path)

    return response


@router.post("/scrape-webextension-docs")
def scrape_webextension_docs(request: WebextensionDocsModel, authorization: Optional[str] = Header(None)):
    email = ''
    try:
        print('try')
        res = requests.get('{}/jwt_secrets?'.format(PG))
        res = json.loads(res.content)
        secret = res[0]['secret']
        print(secret)
        payload = jwt.decode(authorization, secret, algorithms=["HS256"])
        email = payload["email"]
        print(email)
    except:
        return 'Not authorized'
    try:
        print(request)
        user = email
        url = request.url

        platform = request.platform
        print('-------->', url, user)
        temp_response = {}
        response = {}

        ext, loc_path, link = download_webextension_file(url, user, platform)
        text = get_text_from_file(ext, loc_path)
        name = loc_path.split('/')[-1].split('.')[0]
        texts = processor.process({'text': text})

        for i in range(len(texts)):
            texts[i]["meta"]["user"] = user
            texts[i]["meta"]["name"] = name

        document_store_webextension.write_documents(texts)
        if os.path.exists(loc_path):
            os.remove(loc_path)
        temp_response['link'] = link
        print(temp_response)
        return temp_response

    except:
        return {
            "failed": True
        }


@router.post('/scrape-image')
def scrape_image(request: ScrapeImageModel, authorization: Optional[str] = Header(None)):
    extracted = image_extractor(authorization, request.data_uri)
    if extracted[1] == 200:
        return {'ok': True}
    else:
        return {'ok': False, 'message': extracted}
