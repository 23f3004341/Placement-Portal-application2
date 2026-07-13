"""Root launcher kept for simple local runs and Celery imports."""

import os

from backend.app import app, celery, celery_app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(debug=True, port=port, use_reloader=False)
    