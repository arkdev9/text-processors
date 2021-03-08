sudo snap install ffmpeg
sudo apt install youtube-dl
pip install virtualenv
virtualenv -p python venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm
rm venv/bin/punctuator.py
