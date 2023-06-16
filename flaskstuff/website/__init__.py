# when importing website folder
# stuff here will run on startup
from flask import Flask

def create_app():
    app = Flask(__name__)
    # secures cookies/session data related to website
    app.config['SECRET KEY'] = 'sdkjfdkjf'

    # have blueprints that contain different views
    # tells flask where to locate URLs
    from .views import views
    from .auth import auth

    # define new URLs within auth using @auth.route(url)
    # (same for views)
    # any URL defined within views or auth will be prefixed by url_prefix
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    return app