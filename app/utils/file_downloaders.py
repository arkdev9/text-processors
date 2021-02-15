import requests
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from .text_processor import get_file_path

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'app/data/creds.json'
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

def download_webextension_file(url: str, user: str, platform: str) -> (str, str):
    name = url[url.rindex('/')+1:]
    if 'pdf' in url:
        extension = 'pdf'
    elif '.doc' in url:
        extension = 'doc'
    elif '.docx' in url:
        extension = 'docx'
    elif '.txt' in url:
        extension = 'txt'
    elif '.csv' in url:
        extension = 'csv'
    elif '.xls' in url:
        extension = 'xls'
    else:
        extension = url[url.rindex('.')+1:]
    # extension = url[url.rindex('.')+1:]
    print(url)
    # Get access token from workspace creds
    r = requests.get(url, allow_redirects=True)
    print(r)
    localpath = get_file_path(name)
    with open(localpath, 'wb') as f:
        f.write(r.content)

    return (extension, localpath, url)


def download_file(url: str, user: str, access_token: str) -> (str, str):
    if "google" in url:
        print('---------> DRIVE')
        localpath = download_file_gdrive(url)
        extension = localpath[localpath.rindex('.')+1:]
        return (extension, localpath)

    name = url[url.rindex('/')+1:]
    extension = url[url.rindex('.')+1:]
    print(url)
    # Get access token from workspace creds
    r = requests.get(url, allow_redirects=True, headers={
        'Authorization': 'Bearer ' + access_token
    })
    print(r)
    localpath = get_file_path(name)
    with open(localpath, 'wb') as f:
        f.write(r.content)

    return (extension, localpath)


def download_file_gdrive(file_id: str) -> str:
    file_id = file_id.split('/')[-2]
    service = build('drive', 'v3', credentials=credentials)
    request = service.files().get_media(fileId=file_id)
    meta_data_req = service.files().get(fileId=file_id)

    meta = meta_data_req.execute()
    name = meta['name']
    file_ext = meta['mimeType'].split('/').pop()
    localpath = './{}'.format(name)

    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("Download {}".format(int(status.progress() * 100)))

    with open(localpath, 'wb') as f:
        f.write(fh.getbuffer())

    return localpath