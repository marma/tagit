from enum import Enum
from exts import db

class Status(Enum):
    UNKNOWN = 0
    VERIFIED = 1
    BROKEN = 2
    DELETED = 3
    CHANGED = 4

class DatasetType(db.Model):
    __tablename__ = 'datasettype'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)

    def __repr__(self):
        return f'<DatasetType id={self.id}, name={self.name}>'

class Dataset(db.Model):
    __tablename__ = 'dataset'
    id = db.Column(db.Integer, primary_key=True)
    type_id = db.Column(db.Integer, db.ForeignKey('datasettype.id'), nullable=False)
    type = db.relationship('DatasetType', backref=db.backref('datasets', lazy=True))
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True, default='')

    def __repr__(self):
        return f'<Dataset id={self.id}, name={self.name}, status={self.status}>'

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






