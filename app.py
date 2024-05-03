import os
from os.path import join, dirname
from dotenv import load_dotenv

from flask import Flask, request, render_template, url_for, jsonify, redirect
from pymongo import MongoClient
import requests
from bson import ObjectId
from datetime import datetime
app = Flask(__name__)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URI = os.environ.get("MONGODB_URI")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URI)

db = client[DB_NAME]

@app.route('/')
def main():
    wordslist = db.words.find({},{'_id': False})
    words = []
    for word in wordslist:
        definition = word['definitions'][0]['shortdef']
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definition': definition,
        })
    msg = request.args.get('msg')
    return render_template(
        'index.html',
        words=words,
        msg = msg
    )
    #return render_template('index.html')

@app.route('/error/<word>', methods=['GET'])
def wordnotfound(word):
    api_key = '32c6c1d4-4bae-4f38-9b2b-4d2d15969b15'
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word}?key={api_key}'
    response = requests.get(url)
    definitions = response.json()
    if type(definitions[0]) is str:
            suggestions = definitions  
    else:
        suggestions = [definition.get('word') for definition in definitions]  
    return render_template('error.html', word=word, definitions=definitions, suggestions=suggestions)
    #wordslist = list(db.words.find({},{'_id':False}))
    #return jsonify({'wordslist': wordslist})

@app.route('/worderror/<word>', methods=['GET'])
def errorword(word):
    return render_template('errorword.html', word=word)

@app.route('/detail/<keyword>')
def detail(keyword):
    #print(keyword)
    api_key = '32c6c1d4-4bae-4f38-9b2b-4d2d15969b15'
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    definitions = response.json()
    if not definitions:
        return redirect(url_for(
            'errorword',
            word=keyword
        ))

    if type(definitions[0]) is str:
        return redirect(url_for(
            'wordnotfound',
            word=keyword
        ))
    status = request.args.get('status_give', 'new')
    return render_template(
        'detail.html',word=keyword,definitions=definitions,
        status=status
    )
    #return render_template('detail.html', word=keyword)

@app.route('/api/save_word', methods=['POST'])
def save_word():
    json_data = request.get_json()
    word = json_data.get('word_give')
    definitions = json_data.get('definitions_give')
    doc = {
        'word':word,
        'definitions':definitions,
        'date': datetime.now().strftime('%Y%m%d')
    }
    db.words.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg': f'the word {word} was saved'
    })

@app.route('/api/delete_word', methods=['POST'])
def delete_word():
    word = request.form.get('word_give')
    db.words.delete_one({'word': word})
    db.examples.delete_many({'word':word})
    return jsonify({
        'result': 'success',
        'msg': f'the word {word} was delete'
    })

@app.route('/api/get_exs', methods=['GET'])
def get_exs():
    word = request.args.get('word')
    example_data = db.examples.find({'word':word})
    examples = []
    for example in example_data:
        examples.append({
            'example':example.get('example'),
            'id': str(example.get('_id'))
        })
    return jsonify({'result': 'success',
                    'examples': examples})

@app.route('/api/save_ex', methods=['POST'])
def save_ex():
    word = request.form.get('word')
    example = request.form.get('example')
    doc = {
        'word': word,
        'example': example
    }
    db.examples.insert_one(doc)
    return jsonify({'result': 'success',
                    'msg':f'Your example, {example}, was saved!'})


@app.route('/api/delete_ex', methods=['POST'])
def delete_ex():
    id = request.form.get('id')
    word = request.form.get('word')
    db.examples.delete_one({'_id':ObjectId(id)})
    return jsonify({'result': 'success',
                    'msg': f'Your example for the word, {word}, was deleted!'
                    })

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)