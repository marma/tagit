#!/usr/bin/env python3

from flask import Flask,request,render_template,Response
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_migrate import Migrate
from sqlalchemy_utils.functions import database_exists
from sqlalchemy import func
from yaml import load as yload,FullLoader
from os.path import exists,join
from model import DatasetType,Dataset,Tag,TagType,Status,Text,TaggerType,Tagger,db,DatasetTypeView,DatasetView,TextView,TagTypeView,TagView,TaggerView,TaggerTypeView
from utils import tag_content
from collections import Counter
from random import random

def register_extensions(app):
    print('register_extensions')
    db.init_app(app)

    with app.app_context():
        if not database_exists(app.config['SQLALCHEMY_DATABASE_URI']):
            print('Init db with default values')
            db.create_all()
            db.session.add(DatasetType(name='token-classification'))
            db.session.add(DatasetType(name='text-classification'))
            db.session.add(DatasetType(name='question-answering'))
            db.session.add(TagType(name='PER', color='red'))
            db.session.add(TagType(name='ORG', color='orange'))
            db.session.add(TagType(name='LOC', color='yellow'))
            db.session.add(TagType(name='WRK', color='olive'))
            db.session.add(TagType(name='EVN', color='green'))
            db.session.add(TagType(name='OBJ', color='purple'))
            db.session.add(TagType(name='TME', color='pink'))
            db.session.add(TagType(name='MSR', color='pink'))
            db.session.add(TaggerType(name='token-classification'))
            db.session.add(TaggerType(name='text-classification'))
            db.session.add(TaggerType(name='question-answering'))
        else:
            db.create_all()

        db.session.commit()

def create_app():
    app = Flask(__name__)

    #app.config.from_yaml(app.root_path)
    config_path = join(app.root_path, 'config.yml')
    if exists(config_path):
        app.config.update(
            yload(open(config_path), Loader=FullLoader))

    app.jinja_env.line_statement_prefix = '#'
    register_extensions(app)

    app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
    admin = Admin(app, name='tagit', template_mode='bootstrap3')
    admin.add_view(DatasetTypeView(DatasetType, db.session))
    admin.add_view(DatasetView(Dataset, db.session))
    admin.add_view(TextView(Text, db.session))
    admin.add_view(TagTypeView(TagType, db.session))
    admin.add_view(TagView(Tag, db.session))
    admin.add_view(TaggerTypeView(TaggerType, db.session))
    admin.add_view(TaggerView(Tagger, db.session))

    return app

app = create_app()
migrate = Migrate(app, db)

@app.route('/')
def index():
    return Response('', headers={ 'Location': '/datasets/' }), 303


@app.route('/datasets/')
def datasets():
    datasets = datasets=Dataset.query.all()
    counts = { dataset.id:Counter() for dataset in datasets }   

    for dataset_id, status, count in db.session.query(
                                        Text.dataset_id,
                                        Text.status,
                                        func.count(Text.id)).group_by(
                                            Text.dataset_id,
                                            Text.status).all():
        if status in [ Status.UNKNOWN, Status.INCORRECT, Status.VERIFIED ]:
            counts[dataset_id][status.name] = count 
            counts[dataset_id].update({ 'sum': count })

    return render_template('datasets.html', datasets=datasets, counts=counts)


@app.route('/taggers/')
def taggers():
    return render_template('taggers.html', taggers=Tagger.query.all())


@app.route('/dataset/<int:dataset_id>')
def dataset(dataset_id):
    dataset = db.session.query(Dataset).filter(Dataset.id == dataset_id).first()

    return render_template('dataset.html', dataset=dataset)


@app.route('/text/<int:text_id>')
def text(text_id):
    text = db.session.query(Text).filter(Text.id == text_id).first()

    if text:
        return render_template('validate.html', text=text, tagged=tag_content(text.content, text.tags))
    else:
        return 'Not found', 404

@app.route('/dataset/<int:dataset_id>/_random')
def random_text(dataset_id):
    for status in [ Status.UNKNOWN, Status.INCORRECT ]:
        n_texts = db.session.query(Text).filter(Text.status == status).count()

        if n_texts > 0:
            n = int(n_texts*random())
            text = db.session.query(Text).filter(Dataset.id == dataset_id, Text.status == status).limit(1).offset(n).first()

            return Response('', headers={ 'Location': f'/text/{text.id}' }), 303

    return Response('', headers={ 'Location': f'/datasets/' }), 303

@app.route('/dataset/<int:dataset_id>/add', methods=[ 'GET' ])
def add_texts(dataset_id):
    dataset = db.session.query(Dataset).filter(Dataset.id == dataset_id).first()

    return render_template('add_texts.html', dataset=dataset)

@app.route('/dataset/<int:dataset_id>/add', methods=[ 'POST' ])
def post_add_texts(dataset_id):
    def get_type_id(tname, text):
        #print(tname, text)
        for tt in text.dataset.tag_types:
            if tt.name == tname:
                return tt.id

        print(f'warning: tag {tname} does not exist')

    mode = request.form.get('mode', 'line')
    data = request.form.get('data', '')
    status = Status[request.form.get('status', 'unknown').upper()]
    dataset = db.session.query(Dataset).filter(Dataset.id == dataset_id).first()

    if dataset == None:
        return 'Not found', 404

    if mode == 'lines':
        for line in data.split('\n'):
            if line.strip() != '':
                dataset.texts.append(Text(dataset_id=dataset_id, content=line, status=Status.UNKNOWN))

        db.session.commit()
    elif mode == 'conll':
        def combine(chunk):
            l2 = []
            l3 = []
            last_type = None
            for token in chunk:
                if token['word'] in [ '[CLS]', '[SEP]' ]:
                    continue

                if last_type != token['entity'] and l3:
                    l2 += [ { 'word': ' '.join([ x['word'] for x in l3 ]),
                              'entity': last_type } ]
                    l3 = [ token ]
                else:
                    l3 += [ token ]

                last_type = token['entity']

            l2 += [ { 'word': ' '.join([ x['word'] for x in l3 ]), 'entity': last_type } ]            

            return l2


        def chunkit(data):
            chunk = []
            for line in data.split('\n'):
                if line.strip() == '':
                    if chunk != []:
                        yield combine(chunk)
                        chunk = []
                        tags = []
                        i = 0
                else:
                    chunk += [ { 'word': line.split()[0], "entity": line.split()[1] } ]

            if chunk != []:
                yield combine(chunk)

        for chunk in chunkit(data):
            #print(chunk)
            content = ''
            for token in chunk:
                #print(token)
                # ignore 'O' token
                if token['entity'] != 'O':
                    token['start'] = len(content) + (0 if content == '' else 1)
                    token['stop'] = token['start'] + len(token['word'])

                content += (' ' if len(content) != 0 else '') + token['word']

            tags = [ x for x in chunk if x['entity'] != 'O' ]

            # add text
            text = Text(dataset_id=dataset_id, content=content, status=status)
            dataset.texts.append(text)

            # add tags
            for tag in tags:
                tt = get_type_id(tag['entity'], text)
                if tt != None:
                    text.tags.append(
                        Tag(type_id=tt,
                            start=tag['start'],
                            stop=tag['stop']))
        
        db.session.commit()

        #print(text, tags)

    return Response('', headers={ 'Location': f'/dataset/{dataset_id}' }), 303


@app.route('/_validate', methods=[ 'POST' ])
def validate():
    def tag_equals(t1, t2):
        if isinstance(t1, dict):
            x = t1
            t1 = t2
            t2 = x

        return t1.type.name == t2['tag'] and \
               t1.start == t2['start'] and \
               t1.stop == t2['stop']

    def in_tags(tag, tags):
        return any([ tag_equals(t, tag) for t in tags ])

    def get_type_id(tname, text):
        for tt in text.dataset.tag_types:
            if tt.name == tname:
                return tt.id

    data = request.json
    text_id = data['text_id']
    status = data['status']
    text = db.session.query(Text).filter(Text.id == text_id).first()

    if status in [ 'verified' ]:
        tags = data['tags']

        add = []
        delete = []

        for t in tags:
            if not in_tags(t, text.tags):
                add += [ t ]

        for t in text.tags:
            if not in_tags(t, tags):
                    delete += [ t ]

        #print(add)
        #print(delete)

        for t in add:
            text.tags.append(Tag(type_id=get_type_id(t['tag'], text), start=t['start'], stop=t['stop']))

        for t in delete:
            db.session.delete(t)

    if status == 'verified':
        text.status = Status.VERIFIED
    elif status == 'deleted':
        text.status = Status.DELETED
    elif status == 'broken':
        text.status = Status.BROKEN
    elif status == 'incorrect':
        text.status = Status.INCORRECT
    elif status == 'unknown':
        text.status = Status.UNKNOWN
        
    db.session.commit()

    return "OK"

