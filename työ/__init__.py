from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from os import getenv

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql://sspostgres:kakkakakka@localhost:5432/ssflaskapp'
app.config['SECRET_KEY'] = 'thisusfirstflaskapp'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)
bcrypt=Bcrypt(app)

from työ import routes