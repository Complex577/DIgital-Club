from datetime import datetime
import json
import os
from datetime import timedelta

from flask import render_template, request, redirect, url_for, flash, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.quiz_constants import QUIZ_FIELDS_OF_STUDY, QUIZ_MAX_QUESTIONS, QUIZ_DEFAULT_DURATION_MINUTES
from app.quiz_queue import enqueue_quiz_generation
from app.models import Quiz, QuizQuestion, QuizOption, QuizResource
from app.routes import quizmaster_bp
from app.quiz_cleanup import delete_quiz_and_related


def quizmaster_required(f):
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ["quizmaster", "admin"]:
            flash("Quizmaster access required.", "error")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)

    return decorated


def _recover_stale_generation(quiz):
    """
    Prevent quizzes from being stuck forever in queued/generating state.
    """
    now = datetime.utcnow()
    if quiz.status == "queued":
        # Queued but never picked for too long.
        if (quiz.updated_at and now - quiz.updated_at > timedelta(minutes=20)) or (
            quiz.generation_started_at is None and quiz.created_at and now - quiz.created_at > timedelta(minutes=30)
        ):
            quiz.status = "draft"
            quiz.generation_error = "Generation job expired in queue. Please run generate again."
            quiz.generation_completed_at = now
            db.session.commit()
    elif quiz.status == "generating":
        # AI providers can be slow; give a wider safety window.
        if quiz.generation_started_at and now - quiz.generation_started_at > timedelta(minutes=60):
            quiz.status = "draft"
            quiz.generation_error = "Generation timed out. Please run generate again."
            quiz.generation_completed_at = now
            db.session.commit()


def _delete_quiz_resource_file(resource):
    filename = os.path.basename(resource.file_path or "")
    if not filename:
        return
    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], "quiz_resources", filename)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        # Non-blocking cleanup path.
        pass


@quizmaster_bp.route("/")
@login_required
@quizmaster_required
def dashboard():
    my_quizzes = Quiz.query.filter_by(created_by_user_id=current_user.id).order_by(Quiz.created_at.desc()).all()
    for q in my_quizzes:
        _recover_stale_generation(q)
    stats = {
        "total": len(my_quizzes),
        "draft": sum(1 for q in my_quizzes if q.status == "draft"),
        "ready": sum(1 for q in my_quizzes if q.status == "ready"),
        "published": sum(1 for q in my_quizzes if q.status == "published"),
    }
    return render_template("quizmaster/dashboard.html", quizzes=my_quizzes, stats=stats)


@quizmaster_bp.route("/quizzes/create", methods=["GET", "POST"])
@login_required
@quizmaster_required
def quizzes_create():
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        topic = (request.form.get("topic") or "").strip()
        description = (request.form.get("description") or "").strip()
        field_of_study = (request.form.get("field_of_study") or "").strip()
        total_questions = request.form.get("total_questions", type=int) or 10
        mcq_count = request.form.get("mcq_count", type=int) or 8
        tf_count = request.form.get("tf_count", type=int) or 2
        duration_minutes = request.form.get("duration_minutes", type=int) or QUIZ_DEFAULT_DURATION_MINUTES

        if not title or not topic or not field_of_study:
            flash("Title, field of study, and topic are required.", "error")
            return redirect(url_for("quizmaster.quizzes_create"))
        if field_of_study not in QUIZ_FIELDS_OF_STUDY:
            flash("Invalid field of study selected.", "error")
            return redirect(url_for("quizmaster.quizzes_create"))
        if total_questions < 1 or total_questions > QUIZ_MAX_QUESTIONS:
            flash(f"Total questions must be between 1 and {QUIZ_MAX_QUESTIONS}.", "error")
            return redirect(url_for("quizmaster.quizzes_create"))
        if mcq_count + tf_count != total_questions:
            flash("MCQ and True/False distribution must match total questions.", "error")
            return redirect(url_for("quizmaster.quizzes_create"))

        quiz = Quiz(
            title=title,
            topic=topic,
            description=description,
            field_of_study=field_of_study,
            total_questions=total_questions,
            mcq_count=mcq_count,
            tf_count=tf_count,
            duration_minutes=duration_minutes,
            status="draft",
            created_by_user_id=current_user.id,
            generation_meta_json=json.dumps(
                {
                    "total_questions": total_questions,
                    "mcq_count": mcq_count,
                    "tf_count": tf_count,
                }
            ),
        )
        db.session.add(quiz)
        db.session.flush()

        notes = request.files.get("notes_resource")
        if notes and notes.filename:
            filename = secure_filename(notes.filename)
            rel_name = f"quiz_resource_{quiz.id}_{int(datetime.utcnow().timestamp())}_{filename}"
            out_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "quiz_resources")
            os.makedirs(out_dir, exist_ok=True)
            notes.save(os.path.join(out_dir, rel_name))
            db.session.add(
                QuizResource(
                    quiz_id=quiz.id,
                    title="Learning Notes",
                    file_path=rel_name,
                    uploaded_by_user_id=current_user.id,
                )
            )

        db.session.commit()
        flash("Quiz created. Start AI generation.", "success")
        return redirect(url_for("quizmaster.quiz_builder", quiz_id=quiz.id))

    return render_template(
        "quizmaster/create_quiz.html",
        fields_of_study=QUIZ_FIELDS_OF_STUDY,
        max_questions=QUIZ_MAX_QUESTIONS,
        default_duration=QUIZ_DEFAULT_DURATION_MINUTES,
    )


@quizmaster_bp.route("/quizzes/<int:quiz_id>/generate", methods=["POST"])
@login_required
@quizmaster_required
def quiz_generate(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.created_by_user_id != current_user.id and current_user.role != "admin":
        abort(403)
    if quiz.status in ["published", "approved"]:
        flash("Published/approved quiz cannot be regenerated.", "error")
        return redirect(url_for("quizmaster.quiz_builder", quiz_id=quiz.id))
    if quiz.status in ["queued", "generating"]:
        flash("Generation is already running for this quiz.", "info")
        return redirect(url_for("quizmaster.quiz_builder", quiz_id=quiz.id))

    quiz.status = "queued"
    quiz.generation_error = None
    quiz.generation_started_at = None
    quiz.generation_completed_at = None
    db.session.commit()

    job_id = enqueue_quiz_generation(quiz.id)
    if not job_id:
        quiz.status = "draft"
        quiz.generation_error = "Background queue is unavailable. Start Redis + worker and try again."
        db.session.commit()
        flash("Could not queue generation job. Check worker/Redis configuration.", "error")
        return redirect(url_for("quizmaster.quiz_builder", quiz_id=quiz.id))

    quiz.provider_job_id = job_id
    db.session.commit()
    flash("Quiz generation queued in background. You can continue working and refresh status.", "info")
    return redirect(url_for("quizmaster.quiz_builder", quiz_id=quiz.id))


@quizmaster_bp.route("/quizzes/<int:quiz_id>/builder", methods=["GET", "POST"])
@login_required
@quizmaster_required
def quiz_builder(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.created_by_user_id != current_user.id and current_user.role != "admin":
        abort(403)
    _recover_stale_generation(quiz)

    if request.method == "POST":
        action = request.form.get("action")
        if action == "update_question":
            qid = request.form.get("question_id", type=int)
            q = QuizQuestion.query.get_or_404(qid)
            if q.quiz_id != quiz.id:
                abort(400)
            q.scenario = (request.form.get("scenario") or "").strip()
            q.question_text = (request.form.get("question_text") or "").strip()
            q.explanation = (request.form.get("explanation") or "").strip()
            q.difficulty = (request.form.get("difficulty") or "medium").strip()

            options = q.options.order_by(QuizOption.option_key.asc()).all()
            selected_correct_option_id = request.form.get("correct_option_id", type=int)
            valid_option_ids = {opt.id for opt in options}

            for opt in options:
                text_key = f"option_text_{opt.id}"
                if text_key in request.form:
                    opt.option_text = (request.form.get(text_key) or "").strip() or opt.option_text

            if selected_correct_option_id in valid_option_ids:
                for opt in options:
                    opt.is_correct = (opt.id == selected_correct_option_id)

            db.session.commit()
            flash("Question updated.", "success")
        elif action == "delete_question":
            qid = request.form.get("question_id", type=int)
            q = QuizQuestion.query.get_or_404(qid)
            if q.quiz_id != quiz.id:
                abort(400)
            QuizOption.query.filter_by(question_id=q.id).delete(synchronize_session=False)
            db.session.delete(q)
            db.session.commit()
            flash("Question deleted.", "success")
        elif action == "add_question":
            q_type = request.form.get("question_type", "mcq")
            scenario = (request.form.get("scenario") or "").strip()
            question_text = (request.form.get("question_text") or "").strip()
            if not question_text:
                flash("Question text is required.", "error")
            else:
                order_idx = (db.session.query(db.func.max(QuizQuestion.order_index)).filter_by(quiz_id=quiz.id).scalar() or 0) + 1
                q = QuizQuestion(
                    quiz_id=quiz.id,
                    order_index=order_idx,
                    question_type=q_type,
                    scenario=scenario,
                    question_text=question_text,
                    difficulty=(request.form.get("difficulty") or "medium"),
                )
                db.session.add(q)
                db.session.flush()
                if q_type == "true_false":
                    db.session.add(QuizOption(question_id=q.id, option_key="T", option_text="True", is_correct=True))
                    db.session.add(QuizOption(question_id=q.id, option_key="F", option_text="False", is_correct=False))
                else:
                    for k in ["A", "B", "C", "D"]:
                        db.session.add(QuizOption(question_id=q.id, option_key=k, option_text=f"Option {k}", is_correct=(k == "A")))
                db.session.commit()
                flash("Question added.", "success")
        elif action == "submit_for_approval":
            if quiz.questions.count() == 0:
                flash("Add at least one question before submitting.", "error")
            else:
                quiz.status = "pending_approval"
                quiz.submitted_for_approval_at = datetime.utcnow()
                db.session.commit()
                flash("Quiz submitted for admin approval.", "success")
        elif action == "upload_notes":
            notes = request.files.get("notes_resource")
            notes_title = (request.form.get("notes_title") or "Learning Notes").strip() or "Learning Notes"
            replace_existing = (request.form.get("replace_existing") or "").strip() == "1"
            if not notes or not notes.filename:
                flash("Please choose a notes file to upload.", "error")
            else:
                if replace_existing:
                    for existing in quiz.resources.all():
                        _delete_quiz_resource_file(existing)
                        db.session.delete(existing)

                filename = secure_filename(notes.filename)
                rel_name = f"quiz_resource_{quiz.id}_{int(datetime.utcnow().timestamp())}_{filename}"
                out_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "quiz_resources")
                os.makedirs(out_dir, exist_ok=True)
                notes.save(os.path.join(out_dir, rel_name))
                db.session.add(
                    QuizResource(
                        quiz_id=quiz.id,
                        title=notes_title,
                        file_path=rel_name,
                        uploaded_by_user_id=current_user.id,
                    )
                )
                db.session.commit()
                flash("Lecture notes uploaded.", "success")
        elif action == "update_note_title":
            note_id = request.form.get("note_id", type=int)
            note = QuizResource.query.get_or_404(note_id)
            if note.quiz_id != quiz.id:
                abort(400)
            note.title = (request.form.get("notes_title") or "").strip() or "Learning Notes"
            db.session.commit()
            flash("Notes title updated.", "success")
        elif action == "delete_note":
            note_id = request.form.get("note_id", type=int)
            note = QuizResource.query.get_or_404(note_id)
            if note.quiz_id != quiz.id:
                abort(400)
            _delete_quiz_resource_file(note)
            db.session.delete(note)
            db.session.commit()
            flash("Notes removed.", "success")
        return redirect(url_for("quizmaster.quiz_builder", quiz_id=quiz.id))

    questions = quiz.questions.order_by(QuizQuestion.order_index.asc()).all()
    notes_resources = quiz.resources.order_by(QuizResource.uploaded_at.desc()).all()
    return render_template("quizmaster/quiz_builder.html", quiz=quiz, questions=questions, notes_resources=notes_resources)


@quizmaster_bp.route("/quizzes/<int:quiz_id>/delete", methods=["POST"])
@login_required
@quizmaster_required
def quiz_delete(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    if quiz.created_by_user_id != current_user.id and current_user.role != "admin":
        abort(403)
    if quiz.status in ["approved", "published"]:
        flash("Approved/published quizzes can only be deleted by admins.", "warning")
        return redirect(url_for("quizmaster.quiz_builder", quiz_id=quiz.id))

    delete_quiz_and_related(quiz)
    db.session.commit()
    flash("Quiz deleted successfully.", "success")
    return redirect(url_for("quizmaster.dashboard"))
