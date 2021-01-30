#!/usr/bin/env python3

from flask import Flask,request,render_template,Response
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_migrate import Migrate
from sqlalchemy_utils.functions import database_exists
from yaml import load as yload,FullLoader
from os.path import exists,join
from model import DatasetType,Dataset,Tag,TagType,Status,Text,TaggerType,Tagger,db,DatasetTypeView,DatasetView,TextView,TagTypeView,TagView,TaggerView,TaggerTypeView
from utils import tag_content

def register_extensions(app):
    print('register_extensions')
    db.init_app(app)
    
    with app.app_context():
        if not database_exists(app.config['SQLALCHEMY_DATABASE_URI']):
            db.create_all()
            db.session.add(DatasetType(name='token-classification'))
            db.session.add(DatasetType(name='text-classification'))
            db.session.add(TagType(name='PER', color='red'))
            db.session.add(TagType(name='ORG', color='orange'))
            db.session.add(TagType(name='LOC', color='yellow'))
            db.session.add(TagType(name='WRK', color='olive'))
            db.session.add(TagType(name='EVT', color='green'))
            db.session.add(TagType(name='OBJ', color='purple'))
            db.session.add(TagType(name='TME', color='pink'))
            db.session.add(TaggerType(name='NER'))
            db.session.add(TaggerType(name='POS'))
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
    return Response(str(Tag.query.all()), mimetype='text/plain')


@app.route('/text/<int:text_id>')
def text(text_id):
    text = db.session.query(Text).filter(Text.id == text_id).first()

    if text:
        return render_template('validate.html', text=text, tagged=tag_content(text.content, text.tags))
    else:
        return 'Not found', 404


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

        print(add)
        print(delete)

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

    if text:
        if status == 'verified':
            text.status = Status.VERFIFIED
        elif status == 'broken':
            text.status = Status.BROKEN
        elif status == 'delete':
            text.status = Status.DELETED
    else:
        return 'Not found', 404







    
