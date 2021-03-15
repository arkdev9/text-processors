import json
import os
import re
import sys
import textwrap
import uuid
import wave
from itertools import islice
from typing import Optional

import numpy as np
import spacy
from elasticsearch import Elasticsearch
from haystack import Document
from haystack.preprocessor.preprocessor import PreProcessor
from punctuator import Punctuator
from transformers import (ProphetNetConfig, ProphetNetForConditionalGeneration,
                          ProphetNetTokenizer)
from vosk import KaldiRecognizer, Model, SetLogLevel
from youtube_transcript_api import YouTubeTranscriptApi

from ...config import DB_HOST, DB_PORT, DB_PW, DB_USER, ES_CONN_SCHEME
from ..fcm import send_message
from ..summarizer.summarizer import Summarizer
from .utils import download_audio

summarizer_model = Summarizer(
    model_name_or_path="app/models/nlp/sshleifer/distilbart-cnn-12-6")
es = Elasticsearch(["{}://{}:{}".format(ES_CONN_SCHEME, DB_HOST, DB_PORT)],
                   http_auth=(DB_USER, DB_PW), verify_certs=False)
model = Model("app/models/vosk-model-en-us-aspire-0.2")
p = Punctuator('app/models/Demo-Europarl-EN.pcl')


processor = PreProcessor(clean_empty_lines=True,
                         clean_whitespace=True,
                         clean_header_footer=True,
                         split_by="word",
                         split_length=256,
                         split_respect_sentence_boundary=True)
def get_transcript_from_api(video_id):
    transcript=""
    try:
        data = YouTubeTranscriptApi.get_transcript(video_id)
        for dicto in data:
            transcript+=dicto["text"]+" "
        transcript = ''.join([i if ord(i) < 128 else ' ' for i in transcript])
        transcript = re.sub('-', '',transcript)
        transcript = re.sub(' +', ' ',transcript)
        transcript = re.sub(r'\[\w+\]', '',transcript)
        transcript = p.punctuate(transcript)
    except Exception as err:
        print(err)
    
    return transcript

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
    text = get_transcript_from_api(video_id)
    if len(text)==0:
        f_path = download_audio(video_id)
        print(f_path)
        text = vosk_transcribe(f_path)
        os.remove(f_path)
        print('Transcription done')
    return text
    
def store_transcription_to_index(text,video_id,should_summarize):
    if not video_id:
        video_id=""
    source_id = uuid.uuid1()
    indextostore="webextension"
    processed_text = processor.process({'text': text})
    ratio = 0.5
    if ratio > len(text.split())>500:
        ratio = 0.1
    if not should_summarize:
        for doc in processed_text:
            es.index(indextostore, {'text': doc['text'], 'video_id': video_id,'source_id':source_id})
        return source_id,text
    else:
        complete_summary = ""
        for doc in processed_text:
            try:
                part_summary = get_summary_from_text(doc['text'],ratio=ratio)
                es.index(indextostore, {'text': doc['text'], 'video_id': video_id,'source_id':source_id,'summary':part_summary.text})
                complete_summary+=part_summary.text
            except:
                print("FAILED SUMMARIZING THIS DOC")
        return source_id,complete_summary

def transcribe_handler_ext(vid, reg_id):
    try:
        video_id = vid
        text = get_transcript_from_api(video_id)
        print(text)
        if len(text)==0:
            f_path = download_audio(video_id)
            text = vosk_transcribe(f_path)
            os.remove(f_path)
        source_id,text = store_transcription_to_index(text=text,video_id=video_id,should_summarize=False)
        send_message(reg_token=reg_id, title='Transcription done',
                     body="Your transcription was successful", data={'document_id': str(source_id), 'ok': str(True)})
    except:
        send_message(reg_token=reg_id, title="Transcription didn't complete",
                     body="Your transcription wasn't successful", data={'ok': str(False)})


def transcribe_summarize_handler(vid, reg_id, ratio):
    try:
        video_id = vid
        text = get_transcript_from_api(video_id)
        print("YOUTUBE API:",text)
        if len(text)==0:
            f_path = download_audio(video_id)
            text = vosk_transcribe(f_path)
            os.remove(f_path)
        source_id,summary = store_transcription_to_index(text=text,video_id=video_id,should_summarize=True)
        send_message(reg_token=reg_id, title='Summarization done',
                     body="Your Summarization was successful", data={'document_id': str(source_id), 'ok': str(True)})
    except Exception as e:
        print(e)
        send_message(reg_token=reg_id, title="Summarization didn't complete",
                     body="Your Summarization wasn't successful", data={'ok': str(False)})


def upload_summarize_handler(text, reg_id):
    try:
        source_id,summary = store_transcription_to_index(text=text,video_id=None,should_summarize=True)
        send_message(reg_token=reg_id, title="Summarization done",
                     body="Your summarization was successful", data={'document_id': str(source_id), 'ok': str(True)})
    except Exception as e:
        print(e)
        send_message(reg_token=reg_id, title="Summarization didn't complete",
                     body="Your summarization wasn't successful", data={'ok': str(False)})


def get_summary_from_text(text, ratio):
    DOCS = []
    DOCS.append(Document(text=str(text)))
    total_words = len(text.split())
    summary = summarizer_model.predict(documents=DOCS, min_length=int(
        total_words*ratio), max_length=int(total_words * min(1, ratio+0.1)))[0]
    return summary
