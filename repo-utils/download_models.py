import os
import json
import zipfile

from google.oauth2 import service_account
from google.cloud import storage
# GCS Models

credentials = service_account.Credentials.from_service_account_file(
    'repo-utils/nlp-dl-gcs-key.json', scopes=["https://www.googleapis.com/auth/devstorage.read_only"],
)
client = storage.Client('nlp-dl-meroo', credentials=credentials)
bucket = client.get_bucket('vox-vosk-models-nlpdl')

prefix = 'vosk-model-en-us-aspire-0.2'
dl_dir = 'app/models/vosk-model-en-us-aspire-0.2/'
os.makedirs(dl_dir)
blobs = bucket.list_blobs(prefix=prefix)
for blob in blobs:
    filename = blob.name.split('/')[-1]
    blob.download_to_filename(dl_dir + filename)

blob = bucket.get_blob('Demo-Europarl-EN.pcl')
with open('app/models/Demo-Europarl-EN.pcl', 'wb') as f:
    blob.download_to_file(f)
    print("Downloaded {}".format(blob.name))
