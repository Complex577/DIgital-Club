from celery import Celery
from celery.schedules import crontab


def make_celery(app):
    broker_url = app.config.get("REDIS_URL") or ""
    celery = Celery(app.import_name, broker=broker_url, backend=broker_url)
    celery.conf.update(
        timezone=app.config.get("APP_TIMEZONE", "Africa/Nairobi"),
        enable_utc=False,
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
    )

    celery.conf.beat_schedule = {
        "quiz-reminders-every-minute": {
            "task": "quiz_reminders.process_once",
            "schedule": crontab(minute="*"),
        }
    }

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


def create_celery_app():
    from app import create_app

    flask_app = create_app()
    return make_celery(flask_app)
