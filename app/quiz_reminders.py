from datetime import datetime, timedelta

from app import db
from app.models import (
    Quiz,
    QuizAttempt,
    QuizReminderPreference,
    QuizReminderNotification,
)
from app.time_utils import app_now_naive, app_timezone_label
from app.utils import get_notification_service


def process_quiz_reminders_once():
    """
    Process due reminder SMS and missed-attempt tracking once.
    Safe to run repeatedly; reminder logs enforce idempotency per quiz/member.
    """
    now_local = app_now_naive()

    # Resolve reminder outcomes for ended warmups.
    prefs = QuizReminderPreference.query.filter_by(is_enabled=True).all()
    for pref in prefs:
        pending_logs = QuizReminderNotification.query.filter_by(
            member_id=pref.member_id,
            participation_checked=False
        ).all()
        for log in pending_logs:
            quiz_end = None
            if log.quiz and log.quiz.scheduled_start_at:
                quiz_end = log.quiz.scheduled_start_at + timedelta(minutes=(log.quiz.duration_minutes or 0))
            if not quiz_end or now_local < quiz_end:
                continue

            participated = QuizAttempt.query.filter_by(
                quiz_id=log.quiz_id,
                member_id=log.member_id
            ).filter(
                QuizAttempt.status.in_(["submitted", "timed_out", "auto_submitted"])
            ).first() is not None

            log.participation_checked = True
            log.did_participate = participated
            log.checked_at = datetime.utcnow()

            if participated:
                pref.consecutive_missed_count = 0
            else:
                pref.consecutive_missed_count += 1
                if pref.consecutive_missed_count >= 5:
                    pref.is_enabled = False
                    pref.is_blocked = True

    due_quizzes = Quiz.query.filter(
        Quiz.status == "published",
        Quiz.scheduled_start_at.isnot(None)
    ).all()
    due_quizzes = [
        q for q in due_quizzes
        if (q.scheduled_start_at - timedelta(minutes=5)) <= now_local < q.scheduled_start_at
    ]
    if not due_quizzes:
        db.session.commit()
        return

    sender = get_notification_service()
    for pref in QuizReminderPreference.query.filter_by(is_enabled=True, is_blocked=False).all():
        member = pref.member
        if not member or not member.phone:
            continue
        for quiz in due_quizzes:
            exists = QuizReminderNotification.query.filter_by(
                quiz_id=quiz.id,
                member_id=member.id
            ).first()
            if exists:
                continue
            timezone_label = app_timezone_label()
            sms_ok = bool(sender.send_sms(
                member.phone,
                f"Warmup reminder: {quiz.title} starts at {quiz.scheduled_start_at.strftime('%H:%M')} {timezone_label}. Join in 5 minutes."
            ))
            db.session.add(QuizReminderNotification(
                quiz_id=quiz.id,
                member_id=member.id,
                sms_sent=sms_ok
            ))
    db.session.commit()

