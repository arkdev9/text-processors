import os
import sys
import json
import spacy
import pafy
import wave
import textwrap
import numpy as np

from typing import Optional
from vosk import Model, KaldiRecognizer, SetLogLevel
from transformers import ProphetNetTokenizer, ProphetNetForConditionalGeneration, ProphetNetConfig
from punctuator import Punctuator

from .utils import convert_mp4_wav, download_yt


model = Model(
    "app/models/vosk-model-en-us-aspire-0.2")
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
    ext = download_yt(video_id)
    if ext == "FUCK":
        print('Transcription failed because of invalid extension')
        os.remove('{}.{}'.format(video_id, ext))
        return "FUCK"

    convert_mp4_wav(video_id, ext)
    os.remove('{}.{}'.format(video_id, ext))

    text = vosk_transcribe('./{}.wav'.format(video_id))
    os.remove('{}.wav'.format(video_id))
    print('Transcription done')
    return text
