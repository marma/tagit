#!/usr/bin/env python3

from flask import Flask,request,render_template,Response
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from yaml import load as yload,FullLoader
from os.path import exists,join
from model import DatasetType,Dataset,Tag,TagType,Status,Text,db,DatasetTypeView,DatasetView,TextView,TagTypeView,TagView

def register_extensions(app):
    print('register_extensions')
    db.init_app(app)
    with app.app_context():
        db.create_all()

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

    return app

app = create_app()

@app.route('/')
def index():
    return Response(str(Tag.query.all()), mimetype='text/plain')


@app.route('/_init')
def init():
    dt = DatasetType(name='POS')
    d = Dataset(name='SUC 3.0 POS', type=dt)
    t = Text(content='Jag heter Martin.', dataset=d)
    tt = TagType(name='PER')
    tag = Tag(type=tt, text=t, start=10, stop=16)
    
    db.session.add(dt)
    db.session.commit()

    return 'Done'

