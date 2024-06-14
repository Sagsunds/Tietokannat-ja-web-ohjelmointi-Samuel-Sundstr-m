from työ import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    authorized_areas = db.relationship('Area', secondary='area_user', backref='authorized_users')

class Area(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    is_secret = db.Column(db.Boolean, default=False)
    threads = db.relationship('Thread', backref='area', lazy=True)

class Thread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey('area.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    posts = db.relationship('Post', backref='thread', lazy=True, cascade='all, delete-orphan')

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    thread_id = db.Column(db.Integer, db.ForeignKey('thread.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='posts') 

class PrivateArea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    is_secret = db.Column(db.Boolean, default=True)
    password = db.Column(db.String(100))
    threads = db.relationship('PrivateThread', backref='area', lazy=True)
    posts = db.relationship('PrivatePost', backref='area', lazy=True)

class PrivateThread(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey('private_area.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    posts = db.relationship('PrivatePost', backref='private_thread', lazy=True, cascade='all, delete-orphan')


class PrivatePost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    private_thread_id = db.Column(db.Integer, db.ForeignKey('private_thread.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    private_area_id = db.Column(db.Integer, db.ForeignKey('private_area.id'))
    user = db.relationship('User', backref=db.backref('private_posts', lazy=True))


class AreaUser(db.Model):
    __tablename__ = 'area_user'
    area_id = db.Column(db.Integer, db.ForeignKey('area.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
