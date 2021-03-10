import os
import sys
import json
import spacy
import wave
import textwrap
import numpy as np

from elasticsearch import Elasticsearch
from typing import Optional
from vosk import Model, KaldiRecognizer, SetLogLevel
from transformers import ProphetNetTokenizer, ProphetNetForConditionalGeneration, ProphetNetConfig
from punctuator import Punctuator

from ...config import DB_HOST, DB_PORT, DB_USER, DB_PW, ES_CONN_SCHEME
from .utils import download_audio
from ..fcm import send_message
from ..summarizer.summarizer import Summarizer
from haystack import Document

summarizer_model = Summarizer(model_name_or_path="app/models/nlp/sshleifer/distilbart-cnn-12-6")
es = Elasticsearch(["{}://{}:{}".format(ES_CONN_SCHEME, DB_HOST, DB_PORT)],
                   http_auth=(DB_USER, DB_PW), verify_certs=False)
model = Model("app/models/vosk-model-en-us-aspire-0.2")
p = Punctuator('app/models/Demo-Europarl-EN.pcl')


def vosk_transcribe(file_path):
    check = []
    SetLogLevel(0)
    with wave.open(file_path, 'rb') as audio:
        freq = audio.getframerate()
        recognizer = KaldiRecognizer(model, freq)
        total = audio.getnframes()

    # initialize a list to hold chunks
    chunks = []
    # set bytes size to be processed at each iteration:
    chunk_size = 2000

    with open(file_path, 'rb') as audio:
        audio.read(44)  # skip header

        while True:
            # read chunk by chunk
            data = audio.read(chunk_size)
            if len(data) == 0:
                break
            # append text
            if recognizer.AcceptWaveform(data):
                words = json.loads(recognizer.Result())
                chunks.append(words)

        words = json.loads(recognizer.FinalResult())
        chunks.append(words)
        chunks = [t for t in chunks if 'result' in t]
        transcript = [t for t in chunks if len(t['result']) != 0]
        phrases = [t['text'] for t in transcript]
        text = ' '.join(phrases)

    seg_list = []

    data = p.punctuate(text)

    zingzing = ""
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(data)
    for sent in doc.sents:
        zingzing += sent.text
        seg_list.append(sent.text)

    return textwrap.fill(zingzing, 120)


def transcribe_handler(vid):
    video_id = vid
    f_path = download_audio(video_id)
    print(f_path)
    text = vosk_transcribe(f_path)
    os.remove(f_path)
    print('Transcription done')
    return text


def transcribe_handler_ext(vid, reg_id):
    try:
        video_id = vid
        f_path = download_audio(video_id)
        text = vosk_transcribe(f_path)
        os.remove(f_path)
        retted = es.index('webextension', {'text': text, 'video_id': vid})
        send_message(reg_token=reg_id, title='Transcription done',
                     body="Your transcription was successful", data={'transcript_id': retted['_id'], 'ok': str(True)})
    except:
        send_message(reg_token=reg_id, title="Transcription didn't complete",
                     body="Your transcription wasn't successful", data={'ok': str(False)})

def transcribe_handler_ext_summarize(vid, reg_id,ratio):
    try:
        video_id = vid
        f_path = download_audio(video_id)
        text = vosk_transcribe(f_path)
        os.remove(f_path)
        DOCS = []
        total_words = len(text.split())
        DOCS.append(Document(text=str(text)))
        summary = summarizer_model.predict(documents=DOCS, min_length=int(total_words*ratio), max_length=int(total_words * min(1,ratio+0.05)))[0]
        print(summary)
        retted = es.index('webextension', {'text': text, 'video_id': vid,'summary':summary.text})
        send_message(reg_token=reg_id, title='Summarization done',
                     body="Your Summarization was successful", data={'transcript_id': retted['_id'], 'ok': str(True)})
    except Exception as e:
        print(e)
        send_message(reg_token=reg_id, title="Summarization didn't complete",
                     body="Your Summarization wasn't successful", data={'ok': str(False)})