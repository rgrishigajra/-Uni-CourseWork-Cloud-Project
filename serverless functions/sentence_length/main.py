from flask import escape, jsonify
from collections import defaultdict
import requests
import re
from google.cloud import firestore
import json


def sentence_length(request):
    alphabets = "([A-Za-z])"
    prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
    suffixes = "(Inc|Ltd|Jr|Sr|Co)"
    starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
    acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
    websites = "[.](com|net|org|io|gov)"

    def split_into_sentences(text):
        text = " " + text + "  "
        text = text.replace("\n", " ")
        text = re.sub(prefixes, "\\1<prd>", text)
        text = re.sub(websites, "<prd>\\1", text)
        if "Ph.D" in text:
            text = text.replace("Ph.D.", "Ph<prd>D<prd>")
        text = re.sub("\s" + alphabets + "[.] ", " \\1<prd> ", text)
        text = re.sub(acronyms+" "+starters, "\\1<stop> \\2", text)
        text = re.sub(alphabets + "[.]" + alphabets + "[.]" +
                      alphabets + "[.]", "\\1<prd>\\2<prd>\\3<prd>", text)
        text = re.sub(alphabets + "[.]" + alphabets +
                      "[.]", "\\1<prd>\\2<prd>", text)
        text = re.sub(" "+suffixes+"[.] "+starters, " \\1<stop> \\2", text)
        text = re.sub(" "+suffixes+"[.]", " \\1<prd>", text)
        text = re.sub(" " + alphabets + "[.]", " \\1<prd>", text)
        if "”" in text:
            text = text.replace(".”", "”.")
        if "\"" in text:
            text = text.replace(".\"", "\".")
        if "!" in text:
            text = text.replace("!\"", "\"!")
        if "?" in text:
            text = text.replace("?\"", "\"?")
        text = text.replace(".", ".<stop>")
        text = text.replace("?", "?<stop>")
        text = text.replace("!", "!<stop>")
        text = text.replace("<prd>", ".")
        sentences = text.split("<stop>")
        sentences = sentences[:-1]
        sentences = [s.strip() for s in sentences]
        return sentences

    request_json = request.get_json(silent=True)
    if request_json and 'url' in request_json:
        url = request_json['url']
    else:
        url = 'http://www.gutenberg.org/files/1342/1342-0.txt'
    resp = requests.get(url)
    text = resp.text
    sentences = split_into_sentences(text)
    length_frequency = defaultdict(int)
    for i in range(0, 60):
        length_frequency[i] = 0
    for sentence in sentences:
        words = re.findall(r'\w+', sentence)
        l = len(words)
        if l < 60:
            length_frequency[l] += 1

    response = jsonify({
        'frequency': length_frequency
    })
    response.headers.add('Access-Control-Allow-Headers',
                         "Content-Type,Authorization,true")
    response.headers.add('Access-Control-Allow-Methods',
                         'GET,PUT,POST,PATCH,DELETE,OPTIONS')
    response.headers["Access-Control-Allow-Origin"] = "*"
    db = firestore.Client()
    book_id = url.split('/')[-2]
    doc_ref = db.collection(u'books').document(book_id)
    doc_ref.set({
        u'frequency': json.dumps(length_frequency)
    })
    return response


def cached_data(request):
    request_json = request.get_json(silent=True)
    if request_json and 'url' in request_json:
        url = request_json['url']
    else:
        url = 'http://www.gutenberg.org/files/1342/1342-0.txt'
    book_id = url.split('/')[-2]
    db = firestore.Client()
    doc_ref = db.collection(u'books').document(book_id)
    doc = doc_ref.get()
    if doc.exists:
        freq = json.loads(doc.to_dict()['frequency'])
        response = jsonify({
            'success': True,
            'frequency': freq,
        })
    else:
        response = jsonify({
            'success': False
        })

    response.headers.add('Access-Control-Allow-Headers',
                         "Content-Type,Authorization,true")
    response.headers.add('Access-Control-Allow-Methods',
                         'GET,PUT,POST,PATCH,DELETE,OPTIONS')
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response
