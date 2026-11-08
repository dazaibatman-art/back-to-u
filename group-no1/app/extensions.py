from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)

# Configure login manager defaults
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page or perform this action."
login_manager.login_message_category = "info"
