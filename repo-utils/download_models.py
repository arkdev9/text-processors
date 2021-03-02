import os
import zipfile

from google.oauth2 import service_account
from google.cloud import storage
# GCS Models

credentials = service_account.Credentials.from_service_account_file(
    'repo-utils/nlp-dl-gcs-key.json', scopes=["https://www.googleapis.com/auth/devstorage.read_only"],
)
client = storage.Client('nlp-dl-meroo', credentials=credentials)
bucket = client.get_bucket('vox-vosk-models-nlpdl')

blob = bucket.get_blob('vosk-model-en-us-aspire-0.2.zip')
with open('app/models/vosk-model-en-us-aspire-0.2.zip', 'wb') as f:
    blob.download_to_file(f)
    print('Wrote aspire to disk')

with zipfile.ZipFile('app/models/vosk-model-en-us-aspire-0.2.zip', 'r') as zip_ref:
    zip_ref.extractall('app/models/')
    print('Unzipped aspire')
    os.remove('app/models/vosk-model-en-us-aspire-0.2.zip')
    print("Deleted zip of aspire")

blob = bucket.get_blob('Demo-Europarl-EN.pcl')
with open('app/models/Demo-Europarl-EN.pcl', 'wb') as f:
    blob.download_to_file(f)
    print("Downloaded {}".format(blob.name))
