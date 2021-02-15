import os
import textract
import tempfile

from elasticsearch import Elasticsearch
from werkzeug.utils import secure_filename
from haystack.file_converter.docx import DocxToTextConverter
from haystack.file_converter.pdf import PDFToTextConverter

import re
from cleantext import clean

stop_chars = ['.', ' ']
pdf_converter = PDFToTextConverter(
    remove_numeric_tables=True, valid_languages=["en"])
docx_converter = DocxToTextConverter(
    remove_numeric_tables=True, valid_languages=["en"])


def clean_text(text):
    cleaned_text = clean(text,
                         fix_unicode=True,               # fix various unicode errors
                         to_ascii=True,                 # transliterate to closest ASCII representation
                         lower=False,                    # lowercase text
                         # fully strip line breaks as opposed to only normalizing them
                         no_line_breaks=True,
                         no_urls=False,                  # replace all URLs with a special token
                         no_emails=False,                # replace all email addresses with a special token
                         no_phone_numbers=False,         # replace all phone numbers with a special token
                         no_numbers=False,               # replace all numbers with a special token
                         no_digits=False,                # replace all digits with a special token
                         no_currency_symbols=False,      # replace all currency symbols with a special token
                         no_punct=False,
                         lang="en")
    cleaned_text = cleaned_text.replace(r'/(\r\n)+|\r+|\n+|\t+/', "")
    return cleaned_text


def get_file_path(filename):
    file_name = secure_filename(filename)
    return os.path.join(tempfile.gettempdir(), file_name)


def get_text_from_file(extension, localpath):
    if extension == "pdf":
        doc = pdf_converter.convert(localpath)
        text = doc['text']
    elif extension == 'docx':
        doc = docx_converter.convert(localpath)
        text = doc['text']
    else:
        text = textract.process(localpath)
        text = text.decode('utf-8')
    cleaned_text = clean_text(text)
    return cleaned_text
