import ast
import os

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# FastAPI
PROJECT_NAME = os.getenv("PROJECT_NAME", "FastAPI")

# DB
PG = os.getenv("PG", None)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 9200))
DB_USER = os.getenv("DB_USER", "")
DB_PW = os.getenv("DB_PW", "")
DB_INDEX_FEEDBACK = os.getenv("DB_INDEX_FEEDBACK", "label")
ES_CONN_SCHEME = os.getenv("ES_CONN_SCHEME", "http")
TEXT_FIELD_NAME = os.getenv("TEXT_FIELD_NAME", "text")
NAME_FIELD_NAME = os.getenv("NAME_FIELD_NAME", "name")
SEARCH_FIELD_NAME = os.getenv("SEARCH_FIELD_NAME", "text")
FAQ_QUESTION_FIELD_NAME = os.getenv("FAQ_QUESTION_FIELD_NAME", "question")
EMBEDDING_FIELD_NAME = os.getenv("EMBEDDING_FIELD_NAME", None)
EMBEDDING_DIM = os.getenv("EMBEDDING_DIM", None)

# Monitoring
APM_SERVER = os.getenv("APM_SERVER", None)
APM_SERVICE_NAME = os.getenv("APM_SERVICE_NAME", "haystack-backend")
