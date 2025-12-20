from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_login import LoginManager
from app.config import Config

app = Flask(__name__)
app.config.from_object(Config)

bootstrap = Bootstrap5(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

from app import routes