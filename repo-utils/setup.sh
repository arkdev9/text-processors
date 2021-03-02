sudo snap install ffmpeg
pip install virtualenv
virtualenv -p python venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm
rm venv/bin/punctuator.py
