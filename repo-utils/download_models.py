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
from transformers import pipeline
from transformers.models.auto.modeling_auto import AutoModelForSeq2SeqLM
# from transformers import AutoTokenizer
model_name_or_path = "sshleifer/distilbart-cnn-12-6"
tokenizer = model_name_or_path
model = AutoModelForSeq2SeqLM.from_pretrained(pretrained_model_name_or_path=model_name_or_path)
summarizer = pipeline("summarization", model=model, tokenizer=tokenizer, device=-1)
summarizer.save_pretrained(save_directory="app/models/nlp/sshleifer/distilbart-cnn-12-6")