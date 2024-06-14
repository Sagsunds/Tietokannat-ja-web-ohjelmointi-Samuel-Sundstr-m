from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://sspostgres:kakkakakka@localhost:5432/ssflaskapp'
app.config['SECRET_KEY'] = 'thisusfirstflaskapp'
db = SQLAlchemy(app)

from työ import routes