from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from os import getenv

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = getenv("DATABASE_URL").replace("://", "ql://", 1)
#app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql://sspostgres:kakkakakka@localhost:5432/ssflaskapp'
app.config['SECRET_KEY'] = 'thisusfirstflaskapp'
db = SQLAlchemy(app)
bcrypt=Bcrypt(app)

from työ import routes