"""Main Flask application file."""

import os
import sys

from flask import Flask, jsonify
from flask_security import Security, SQLAlchemyUserDatastore


BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
BASE_DIR = os.path.abspath(os.path.join(BACKEND_DIR, os.pardir))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.celery_app import celery_init_app
from backend.config import Config, STATIC_DIR, TEMPLATES_DIR
from backend.create_tables import create_tables
from backend.extensions import cache, db, login_manager, mail, migrate
from backend.models import Role, User


def unauthorized_api_request():
    return jsonify({"ok": False, "message": "Authentication required."}), 401


def load_user(user_id):
    try:
        from backend.models import User
        user = User.query.filter_by(fs_uniquifier=str(user_id)).first()
        if user:
            return user
        return User.query.get(int(user_id))
    except Exception:
        return None


def create_app(test_config=None):
    app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.config["EXPORT_DIR"], exist_ok=True)

    db.init_app(app)
    cache.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    Security(app, user_datastore)
    login_manager.user_loader(load_user)
    login_manager.unauthorized_handler(unauthorized_api_request)
    celery = celery_init_app(app)

    from backend.routes import main as main_blueprint

    app.register_blueprint(main_blueprint)

    with app.app_context():
        try:
            from backend import tasks

            del tasks
            create_tables(user_datastore)
        except Exception as exc:
            print(f"Database bootstrap skipped: {exc}")

    app.extensions["celery"] = celery
    return app


app = create_app()
celery_app = app.extensions["celery"]
celery = celery_app


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", "5000")))
