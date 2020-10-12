from flask import Flask
from flask_bootstrap import Bootstrap
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager

from fwmanagement.admin_pages import admin_pages
from fwmanagement.bsw_pages import bsw_pages

app = Flask(__name__)
csrf = CSRFProtect(app)
# api = Api(app)
app.config.from_object("config")
app.jinja_env.globals.update(int=int, abs=abs, enumerate=enumerate)
Bootstrap(app)

app.debug = True

app.register_blueprint(admin_pages, url_prefix="/admin")
app.register_blueprint(bsw_pages, url_prefix="/bsw")

login_manager = LoginManager(app)
login_manager.login_view = "admin_pages.login"
from fwmanagement import sichten
