import os
import threading
import uuid
from flask import current_app


def enqueue_quiz_generation(quiz_id):
    """Queue quiz generation in RQ. Returns job id, or None when queue is unavailable."""
    try:
        import redis
        from rq import Queue
        from rq.retry import Retry

        redis_url = current_app.config.get("REDIS_URL") or os.environ.get("REDIS_URL")
        if not redis_url:
            current_app.logger.error("Quiz queue unavailable: REDIS_URL not configured")
            return None

        conn = redis.from_url(redis_url)
        conn.ping()
        q = Queue("quiz_generation", connection=conn, default_timeout=900)
        job = q.enqueue(
            "app.quiz_tasks.run_quiz_generation_task",
            quiz_id,
            retry=Retry(max=2, interval=[30, 120]),
            result_ttl=86400,
            failure_ttl=604800,
        )
        return job.id
    except Exception as exc:
        current_app.logger.exception("Failed to enqueue quiz generation via RQ: %s", exc)

        # Development-safe non-blocking fallback (used when RQ isn't available, e.g. Windows local env).
        try:
            from app.quiz_tasks import run_quiz_generation_task

            job_id = f"thread-{uuid.uuid4().hex[:12]}"
            logger = current_app.logger

            def _runner():
                try:
                    run_quiz_generation_task(quiz_id)
                except Exception:
                    logger.exception("Thread fallback generation failed for quiz_id=%s", quiz_id)

            t = threading.Thread(target=_runner, daemon=True, name=f"quiz-gen-{quiz_id}")
            t.start()
            logger.warning("Using thread fallback for quiz generation (job_id=%s).", job_id)
            return job_id
        except Exception:
            current_app.logger.exception("Thread fallback enqueue also failed.")
            return None
