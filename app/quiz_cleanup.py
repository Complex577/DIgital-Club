import os
from flask import current_app

from app import db
from app.models import (
    Quiz,
    QuizAttempt,
    QuizAttemptAnswer,
    QuizLeaderboard,
    QuizOption,
    QuizQuestion,
    QuizReminderNotification,
    QuizResource,
    QuizViolation,
    RewardTransaction,
)


def _delete_quiz_resource_file(resource):
    if not resource or not resource.file_path:
        return
    file_path = os.path.join(
        current_app.config["UPLOAD_FOLDER"], "quiz_resources", resource.file_path
    )
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except OSError:
        pass


def delete_quiz_and_related(quiz: Quiz):
    """Delete quiz and all related records/files in a safe order."""
    if not quiz:
        return

    quiz_id = quiz.id

    # Remove resource files first
    for resource in QuizResource.query.filter_by(quiz_id=quiz_id).all():
        _delete_quiz_resource_file(resource)

    # Remove reminders for this quiz
    QuizReminderNotification.query.filter_by(quiz_id=quiz_id).delete(
        synchronize_session=False
    )

    # Delete attempt answers and violations (join via attempts)
    attempt_subq = db.session.query(QuizAttempt.id).filter_by(quiz_id=quiz_id).subquery()
    QuizAttemptAnswer.query.filter(
        QuizAttemptAnswer.attempt_id.in_(attempt_subq)
    ).delete(synchronize_session=False)
    QuizViolation.query.filter(
        QuizViolation.attempt_id.in_(attempt_subq)
    ).delete(synchronize_session=False)

    # Leaderboard + attempts
    QuizLeaderboard.query.filter_by(quiz_id=quiz_id).delete(synchronize_session=False)
    QuizAttempt.query.filter_by(quiz_id=quiz_id).delete(synchronize_session=False)

    # Delete options + questions
    question_subq = db.session.query(QuizQuestion.id).filter_by(quiz_id=quiz_id).subquery()
    QuizOption.query.filter(QuizOption.question_id.in_(question_subq)).delete(
        synchronize_session=False
    )
    QuizQuestion.query.filter_by(quiz_id=quiz_id).delete(synchronize_session=False)

    # Delete resources DB rows
    QuizResource.query.filter_by(quiz_id=quiz_id).delete(synchronize_session=False)

    # Delete reward transactions linked to this quiz (use reason convention)
    RewardTransaction.query.filter(
        RewardTransaction.transaction_type == "quiz",
        RewardTransaction.reason.ilike(f"Quiz {quiz_id} -%"),
    ).delete(synchronize_session=False)

    # Finally delete the quiz
    db.session.delete(quiz)
