import os

from flask import Flask

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    # シークレットキーと、データベースパスを設定
    app.config.from_mapping(
        SECRET_KEY = "dev",
        DATABASE = os.path.join(app.instance_path, "flask.sqlite")
    )


    if test_config is None:
        # configがなくてもエラーを発生させない
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)
    
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from .import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    from . import manager
    from . import index, edit, book_delete
    app.register_blueprint(manager.bp)
    app.add_url_rule("/", endpoint="index")
    
    return app
