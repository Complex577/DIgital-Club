"""
Background worker for warmup reminder SMS.

Run:
  .\\.venv\\Scripts\\python.exe scripts/quiz_reminder_worker.py

Env:
  QUIZ_REMINDER_INTERVAL_SECONDS=30
"""

import os
import time

from app import create_app, db
from app.quiz_reminders import process_quiz_reminders_once


def main():
    app = create_app()
    interval = int(os.getenv("QUIZ_REMINDER_INTERVAL_SECONDS", "30"))
    with app.app_context():
        while True:
            try:
                process_quiz_reminders_once()
            except Exception:
                db.session.rollback()
                app.logger.exception("quiz reminder worker iteration failed")
            time.sleep(max(10, interval))


if __name__ == "__main__":
    main()

