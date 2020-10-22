import os
from flask import Flask
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate


SECRET_KEY = os.urandom(32)

# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Enable debug mode.
DEBUG = True


# App Config.
app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app, session_options={"expire_on_commit": False})

# IMPLEMENT DATABASE URL
SQLALCHEMY_DATABASE_URI = r'postgresql://postgres:pass@localhost:5432/fyyurapp'

# Connect to a local postgresql database.
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# maigrations
migrate = Migrate(app, db)


