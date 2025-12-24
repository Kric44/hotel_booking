from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager
from app.config import Config

app = Flask(__name__)
app.config.from_object(Config)
bootstrap = Bootstrap5(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

from app import routes