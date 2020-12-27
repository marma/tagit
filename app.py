#!/usr/bin/env python3

from flask import Flask,request,render_template,Response
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from sqlalchemy_utils.functions import database_exists
from yaml import load as yload,FullLoader
from os.path import exists,join
from model import DatasetType,Dataset,Tag,TagType,Status,Text,db,DatasetTypeView,DatasetView,TextView,TagTypeView,TagView

def register_extensions(app):
    print('register_extensions')
    db.init_app(app)

    if not database_exists(app.config['SQLALCHEMY_DATABASE_URI']):
        with app.app_context():
            db.create_all()
            db.session.add(DatasetType(name='token-classification'))
            db.session.add(DatasetType(name='text-classification'))
            db.session.add(TagType(name='PER'))
            db.session.add(TagType(name='ORG'))
            db.session.add(TagType(name='LOC'))
            db.session.add(TagType(name='WRK'))
            db.session.add(TagType(name='EVT'))
            db.session.add(TagType(name='OBJ'))
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

    return app

app = create_app()

@app.route('/')
def index():
    return Response(str(Tag.query.all()), mimetype='text/plain')


@app.route('/text/<int:text_id>')
def validate(text_id):
    text = db.session.query(Text).filter(Text.id == text_id).first()

    if text:
        return render_template('validate.html', text=text)
    else:
        return 'Not found', 404
    
