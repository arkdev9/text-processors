from os import path
import json
import urllib
import isodate
import subprocess
import youtube_dl
import requests


def convert_mp4_wav(video_id, ext):
    command = "ffmpeg -i {}.{} -vn -ar 16000 -ac 1 {}.wav".format(
        video_id, ext, video_id)
    subprocess.call(command, shell=True)


def download_yt(video_id):
    ydl = youtube_dl.YoutubeDL({'outtmpl': '%(id)s.%(ext)s'})
    with ydl:
        results = ydl.download(
            ['http://www.youtube.com/watch?v={}'.format(video_id)])

    if path.exists('./{}.mkv'.format(video_id)):
        return 'mkv'
    elif path.exists('./{}.mp4'.format(video_id)):
        return 'mp4'
    elif path.exists('./{}.webm'.format(video_id)):
        return 'webm'
    else:
        return "FUCK"


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
