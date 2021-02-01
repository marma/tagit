from enum import Enum
from exts import db
from flask_admin.contrib.sqla import ModelView
from sqlalchemy_utils import ColorType

class Status(Enum):
    UNKNOWN = 0
    VERIFIED = 1
    INCORRECT = 2
    BROKEN = 3
    DELETED = 4
    CHANGED = 5
    GENERATED = 6
    PARTIAL = 7

class DatasetType(db.Model):
    __tablename__ = 'datasettype'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)

    def __repr__(self):
        return f'<DatasetType id={self.id}, name={self.name}>'

dataset_tagtype = db.Table('dataset_tagtype', db.Model.metadata,
    db.Column('dataset_id', db.Integer, db.ForeignKey('dataset.id')),
    db.Column('tagtype_id', db.Integer, db.ForeignKey('tagtype.id'))
)

class Dataset(db.Model):
    __tablename__ = 'dataset'
    id = db.Column(db.Integer, primary_key=True)
    type_id = db.Column(db.Integer, db.ForeignKey('datasettype.id'), nullable=False)
    type = db.relationship('DatasetType', backref=db.backref('datasets', lazy=True))
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True, default='')
    tag_types = db.relationship("TagType", secondary=dataset_tagtype)
    tagger_id = db.Column(db.Integer, db.ForeignKey('tagger.id'), nullable=True)
    tagger = db.relationship('Tagger', backref=db.backref('datasets'), lazy=True)

    def __repr__(self):
        return f'<Dataset id={self.id}, name={self.name}>'

class Text(db.Model):
    __tablename__ = 'text'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum(Status), nullable=False, default=Status.UNKNOWN)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=False)
    dataset = db.relationship('Dataset', backref=db.backref('texts'), lazy=True)
    
    def __repr__(self):
        return f'<Text id={self.id}, status={self.status}, dataset_id={self.dataset.id}, content="{self.content}">'

class TagType(db.Model):
    __tablename__ = 'tagtype'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16), nullable=False)
    description = db.Column(db.Text, nullable=True)
    color = db.Column(ColorType, nullable=False, default='#ff3f00')

    def __repr__(self):
        return f'<TagType id={self.id}, name={self.name}>'

class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)
    type_id = db.Column(db.Integer, db.ForeignKey('tagtype.id'), nullable=False)
    type = db.relationship('TagType', backref=db.backref('tags', lazy=True))
    text_id = db.Column(db.Integer, db.ForeignKey('text.id'), nullable=False)
    text = db.relationship('Text', backref=db.backref('tags', lazy=True))
    start = db.Column(db.Integer, nullable=False)
    stop = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Tag id={self.id}, start={self.start}, stop={self.stop}, type={self.type}, text_id={self.text.id}>'

class TaggerType(db.Model):
    __tablename__ = 'taggertype'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(16), unique=True, nullable=False)    
    description = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<TaggerType id={self.id}, name={self.name}>'

class Tagger(db.Model):
    __tablename__ = 'tagger'
    id = db.Column(db.Integer, primary_key=True)
    type_id = db.Column(db.Integer, db.ForeignKey('taggertype.id'), nullable=False)
    type = db.relationship('TaggerType', backref=db.backref('taggers', lazy=True))
    name = db.Column(db.String(16), unique=True, nullable=False)
    url = db.Column(db.String(1024), nullable=True)
    description = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Tagger id={self.id}, name={self.name}, description={self.description}>'


class DatasetTypeView(ModelView):
    column_display_pk = True
    form_columns = ('name',)

class DatasetView(ModelView):
    column_display_pk = True
    form_columns = ('name', 'description', 'type', 'tag_types', 'tagger')
    column_list = ('id', 'name', 'description', 'type', 'tag_types')

class TextView(ModelView):
    column_display_pk = True
    form_columns = ('dataset', 'content', 'status')
    column_list = ('id', 'content', 'status', 'dataset')

class TagTypeView(ModelView):
    column_display_pk = True
    form_columns = ('name', 'description', 'color')

class TagView(ModelView):
    column_display_pk = True
    form_columns = ('type', 'text_id', 'start', 'stop')
    column_list = ('id', 'start', 'stop', 'type', 'text')

class TaggerTypeView(ModelView):
    column_display_pk = True
    form_columns = ('name', 'description')

class TaggerView(ModelView):
    column_display_pk = True
    form_columns = ('type', 'name', 'url', 'description')
    column_list = ('id', 'type', 'name', 'description')






