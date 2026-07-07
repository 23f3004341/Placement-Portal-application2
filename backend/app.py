import os
import sys

BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
BASE_DIR = os.path.abspath(os.path.join(BACKEND_DIR, os.pardir))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.init import create_app

app = create_app()
celery_app = app.extensions["celery"]
celery = celery_app


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", "5000")))
