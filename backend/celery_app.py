"""Small Celery setup file, matching the viva-friendly project layout."""

from celery import Celery, Task


_flask_app = None


class FlaskTask(Task):
    def __call__(self, *args, **kwargs):
        if _flask_app is None:
            return self.run(*args, **kwargs)
        with _flask_app.app_context():
            return self.run(*args, **kwargs)


celery = Celery("placement_portal", task_cls=FlaskTask)
celery_app = celery


def celery_init_app(app):
    global _flask_app
    _flask_app = app
    celery.conf.update(app.config["CELERY"])
    celery.conf.beat_schedule = app.config["CELERY_BEAT_SCHEDULE"]
    celery.set_default()
    app.extensions["celery"] = celery
    return celery


if __name__ != "__main__":
    try:
        from backend.app import app

        celery = app.extensions["celery"]
        celery_app = celery
    except Exception:
        pass
