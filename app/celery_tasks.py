from app.celery_app import create_celery_app
from app.quiz_reminders import process_quiz_reminders_once


celery = create_celery_app()


@celery.task(name="quiz_reminders.process_once")
def process_quiz_reminders_task():
    return process_quiz_reminders_once()
