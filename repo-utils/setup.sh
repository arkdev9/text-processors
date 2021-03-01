pip install virtualenv
virtualenv -p python venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
rm venv/bin/punctuator.py
