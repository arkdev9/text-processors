import os
import json
import urllib
import isodate
import subprocess
import youtube_dl
import requests


def get_audio_url(youtube_url: str) -> str:
    print(os.environ)
    command = ['youtube-dl', '--youtube-skip-dash-manifest', '-g', youtube_url]
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    print(err)
    print('out', out)
    urls = out.split(b'\n')
    print(urls)
    audio_url = urls[1].decode('utf-8')
    return audio_url


def download_audio(vid: str):
    youtube_url = 'https://youtube.com/watch?v={}'.format(vid)
    cmd_str = 'ffmpeg -ss 0 -i "{}" -ss 0 -t 300 {}.mp3'.format(
        get_audio_url(youtube_url), vid)
    print(cmd_str)
    os.system(cmd_str)

    cmd_str = 'ffmpeg -i {}.mp3 {}.wav'.format(vid, vid)
    os.system(cmd_str)
    os.remove('{}.mp3'.format(vid))
    return '{}.wav'.format(vid)


def get_video_duration(video_id: str):
    api_key = "AIzaSyBTR1FSGH1Rptk0kAtzeABPFeIvJ3NhFyM"
    searchUrl = "https://www.googleapis.com/youtube/v3/videos?id=" + \
        video_id+"&key="+api_key+"&part=contentDetails"
    response = requests.get(searchUrl)
    data = response.json()
    print(data)
    all_data = data['items']
    contentDetails = all_data[0]['contentDetails']
    duration = contentDetails['duration']
    dur = isodate.parse_duration(duration)
    return dur.total_seconds()
