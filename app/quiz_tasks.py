import json
import random
import re
from datetime import datetime

import requests

from app import create_app, db
from app.models import Quiz, QuizQuestion, QuizOption, SystemSettings


def _deepseek_generate(prompt, api_key):
    endpoint = "https://api.deepseek.com/chat/completions"
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Generate practical scenario-based technical quiz questions in JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.3,
        "max_tokens": 3500,
        "response_format": {"type": "json_object"},
    }
    resp = requests.post(
        endpoint,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def _gemini_generate(prompt, api_key):
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 3500,
            "responseMimeType": "application/json",
        },
    }
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    model_candidates = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-flash-latest",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash-001",
    ]

    last_error = None
    for model in model_candidates:
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=120)
        if resp.status_code == 404:
            last_error = RuntimeError(f"Gemini model not found: {model}")
            continue
        resp.raise_for_status()
        data = resp.json()
        parts = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [])
        )
        text = "".join(p.get("text", "") for p in parts if isinstance(p, dict)).strip()
        if text:
            return text
        last_error = RuntimeError(f"Gemini returned empty content for model: {model}")

    if last_error:
        raise last_error
    raise RuntimeError("Gemini generation failed: no usable model response")


def _fallback_questions(field_of_study, topic, total_questions, mcq_count, tf_count):
    mcq_templates = [
        ("Latency spikes after a release", "Which first action gives the highest diagnostic value?"),
        ("A teammate reports intermittent authentication failures", "What is the best immediate troubleshooting step?"),
        ("Error rates increased in production", "Which response best balances speed and safety?"),
        ("A critical feature must be deployed today", "Which deployment strategy minimizes blast radius?"),
        ("Logs show a sudden CPU surge", "What should you verify first to avoid false assumptions?"),
    ]
    tf_templates = [
        "A rollback plan reduces production incident impact.",
        "Security controls can be postponed if deadlines are tight.",
        "Monitoring without alert thresholds is usually sufficient.",
        "Least-privilege access lowers breach severity.",
        "Post-incident reviews improve long-term reliability.",
    ]

    rows = []
    for i in range(1, total_questions + 1):
        if i <= mcq_count:
            tpl = mcq_templates[(i - 1) % len(mcq_templates)]
            correct_key = ["A", "B", "C", "D"][(i - 1) % 4]
            option_bank = {
                "A": "Inspect logs/metrics and isolate the failing path",
                "B": "Restart all services immediately",
                "C": "Disable alerts to reduce noise",
                "D": "Defer investigation to next sprint",
            }
            rows.append(
                {
                    "question_type": "mcq",
                    "scenario": f"{field_of_study}: {tpl[0]} in topic '{topic}'.",
                    "question_text": tpl[1],
                    "difficulty": "medium",
                    "options": [
                        {"key": "A", "text": option_bank["A"], "correct": correct_key == "A"},
                        {"key": "B", "text": option_bank["B"], "correct": correct_key == "B"},
                        {"key": "C", "text": option_bank["C"], "correct": correct_key == "C"},
                        {"key": "D", "text": option_bank["D"], "correct": correct_key == "D"},
                    ],
                    "explanation": "Start with evidence-backed diagnosis before high-risk actions.",
                }
            )
        else:
            tf_idx = i - mcq_count - 1
            statement = tf_templates[tf_idx % len(tf_templates)]
            true_is_correct = (i % 2 == 1)
            rows.append(
                {
                    "question_type": "true_false",
                    "scenario": f"{field_of_study} scenario on '{topic}'.",
                    "question_text": statement,
                    "difficulty": "easy",
                    "options": [
                        {"key": "T", "text": "True", "correct": true_is_correct},
                        {"key": "F", "text": "False", "correct": not true_is_correct},
                    ],
                    "explanation": "Evaluate against standard software engineering and security practices.",
                }
            )
    random.shuffle(rows)
    return rows


def _prompt_for_quiz_batch(quiz, batch_total, batch_mcq, batch_tf):
    return (
        "Return STRICT JSON only as an array of question objects. No markdown, no commentary. "
        "Each object must include: question_type (mcq|true_false), scenario, question_text, difficulty, explanation, options[]. "
        "Each option needs keys: key, text, correct (boolean). "
        f"Generate exactly {batch_total} questions for field '{quiz.field_of_study}' and topic '{quiz.topic}'. "
        f"Exactly {batch_mcq} MCQ and {batch_tf} true_false. "
        "MCQ must contain exactly options A,B,C,D with only one correct=true. "
        "True/False must contain exactly T and F with only one correct=true. "
        "Questions must be practical, scenario-based, and focused on software engineering decision-making."
    )


def _split_counts(total, mcq, tf, batch_size=10):
    plan = []
    remaining_total = total
    remaining_mcq = mcq
    remaining_tf = tf
    while remaining_total > 0:
        size = min(batch_size, remaining_total)
        mcq_in_batch = min(remaining_mcq, size)
        tf_in_batch = size - mcq_in_batch
        if tf_in_batch > remaining_tf:
            tf_in_batch = remaining_tf
            mcq_in_batch = size - tf_in_batch
        plan.append((size, mcq_in_batch, tf_in_batch))
        remaining_total -= size
        remaining_mcq -= mcq_in_batch
        remaining_tf -= tf_in_batch
    return plan


def _strip_code_fences(text):
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_-]*", "", cleaned).strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
    return cleaned


def _extract_first_json_array(text):
    start = text.find("[")
    if start < 0:
        return None
    depth = 0
    in_str = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def _recover_objects_from_truncated_array(text):
    # Best-effort salvage: parse complete top-level object chunks from a truncated JSON array.
    start = text.find("[")
    if start < 0:
        return []
    i = start + 1
    chunks = []
    depth = 0
    in_str = False
    escaped = False
    obj_start = None
    while i < len(text):
        ch = text[i]
        if in_str:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_str = False
            i += 1
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                obj_start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and obj_start is not None:
                    chunks.append(text[obj_start : i + 1])
                    obj_start = None
        i += 1

    out = []
    for chunk in chunks:
        try:
            obj = json.loads(chunk)
            if isinstance(obj, dict):
                out.append(obj)
        except Exception:
            continue
    return out


def _parse_generated_questions(raw_text):
    cleaned = _strip_code_fences(raw_text)

    # Direct JSON parse first.
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict) and isinstance(parsed.get("questions"), list):
            return parsed["questions"]
    except Exception:
        pass

    # Attempt to extract a valid top-level JSON array from mixed text.
    arr = _extract_first_json_array(cleaned)
    if arr:
        try:
            parsed = json.loads(arr)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass

    # Truncated payload recovery.
    recovered = _recover_objects_from_truncated_array(cleaned)
    if recovered:
        return recovered

    raise ValueError("Failed to parse AI response JSON")


def _extract_questions_lenient(raw_text):
    """
    Provider-agnostic tolerant extraction:
    never raises, returns [] on failure.
    """
    try:
        rows = _parse_generated_questions(raw_text)
        return rows if isinstance(rows, list) else []
    except Exception:
        return []


def _normalize_mcq_options(options):
    keyed = {}
    for opt in options or []:
        key = str(opt.get("key", "")).strip().upper()
        if key in {"A", "B", "C", "D"} and key not in keyed:
            keyed[key] = {
                "key": key,
                "text": (opt.get("text") or f"Option {key}").strip() or f"Option {key}",
                "correct": bool(opt.get("correct", opt.get("is_correct", False))),
            }
    for key in ["A", "B", "C", "D"]:
        if key not in keyed:
            keyed[key] = {"key": key, "text": f"Option {key}", "correct": False}

    values = [keyed[k] for k in ["A", "B", "C", "D"]]
    if sum(1 for v in values if v["correct"]) != 1:
        seed_text = "".join(v["text"] for v in values)
        pick = (sum(ord(c) for c in seed_text) % 4) if seed_text else 0
        for v in values:
            v["correct"] = False
        values[pick]["correct"] = True
    return values


def _normalize_tf_options(options):
    t_opt = None
    f_opt = None
    for opt in options or []:
        key = str(opt.get("key", "")).strip().upper()
        if key == "T" and t_opt is None:
            t_opt = {"key": "T", "text": (opt.get("text") or "True").strip() or "True", "correct": bool(opt.get("correct", opt.get("is_correct", False)))}
        if key == "F" and f_opt is None:
            f_opt = {"key": "F", "text": (opt.get("text") or "False").strip() or "False", "correct": bool(opt.get("correct", opt.get("is_correct", False)))}
    if t_opt is None:
        t_opt = {"key": "T", "text": "True", "correct": True}
    if f_opt is None:
        f_opt = {"key": "F", "text": "False", "correct": False}
    if int(bool(t_opt["correct"])) + int(bool(f_opt["correct"])) != 1:
        seed_text = (t_opt.get("text", "") + f_opt.get("text", "")).strip()
        choose_true = (sum(ord(c) for c in seed_text) % 2 == 0) if seed_text else True
        t_opt["correct"] = choose_true
        f_opt["correct"] = not choose_true
    return [t_opt, f_opt]


def _normalize_questions(rows, expected_total, expected_mcq, expected_tf, field_of_study, topic):
    normalized = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        question_type = (row.get("question_type") or "mcq").strip().lower()
        if question_type in {"true/false", "true-false", "tf"}:
            question_type = "true_false"
        if question_type not in {"mcq", "true_false"}:
            question_type = "mcq"

        question_text = (row.get("question_text") or "").strip()
        if not question_text:
            continue

        if question_type == "mcq":
            options = _normalize_mcq_options(row.get("options") or [])
            correct_answer_key = str(row.get("correct_answer", "")).strip().upper()
            if correct_answer_key in {"A", "B", "C", "D"}:
                for opt in options:
                    opt["correct"] = (opt["key"] == correct_answer_key)
        else:
            options = _normalize_tf_options(row.get("options") or [])
            correct_answer_key = str(row.get("correct_answer", "")).strip().upper()
            if correct_answer_key in {"T", "F", "TRUE", "FALSE"}:
                normalized_key = "T" if correct_answer_key in {"T", "TRUE"} else "F"
                for opt in options:
                    opt["correct"] = (opt["key"] == normalized_key)

        normalized.append(
            {
                "question_type": question_type,
                "scenario": (row.get("scenario") or "").strip(),
                "question_text": question_text,
                "difficulty": (row.get("difficulty") or "medium").strip().lower(),
                "explanation": (row.get("explanation") or "").strip(),
                "options": options,
            }
        )

    mcq_rows = [r for r in normalized if r["question_type"] == "mcq"]
    tf_rows = [r for r in normalized if r["question_type"] == "true_false"]

    # Enforce expected distribution and top-up from deterministic fallback.
    selected = mcq_rows[:expected_mcq] + tf_rows[:expected_tf]
    if len(selected) < expected_total:
        missing_total = expected_total - len(selected)
        selected_mcq = sum(1 for r in selected if r["question_type"] == "mcq")
        selected_tf = sum(1 for r in selected if r["question_type"] == "true_false")
        fb = _fallback_questions(
            field_of_study,
            topic,
            missing_total,
            max(0, expected_mcq - selected_mcq),
            max(0, expected_tf - selected_tf),
        )
        selected.extend(fb)

    return selected[:expected_total]


def run_quiz_generation_task(quiz_id):
    app = create_app()
    with app.app_context():
        quiz = Quiz.query.get(quiz_id)
        if not quiz:
            return

        quiz.status = "generating"
        quiz.generation_started_at = datetime.utcnow()
        quiz.generation_error = None
        db.session.commit()

        try:
            provider = (SystemSettings.get_setting("quiz_ai_provider", "deepseek") or "deepseek").lower()
            deepseek_key = SystemSettings.get_secret_setting("deepseek_api_key", "") or ""
            gemini_key = SystemSettings.get_secret_setting("gemini_api_key", "") or ""

            plans = _split_counts(quiz.total_questions, quiz.mcq_count, quiz.tf_count, batch_size=10)
            aggregated_rows = []
            total_batches = len(plans)
            batch_parse_failures = 0

            for batch_index, (batch_total, batch_mcq, batch_tf) in enumerate(plans, start=1):
                prompt = _prompt_for_quiz_batch(quiz, batch_total, batch_mcq, batch_tf)

                if provider == "gemini" and gemini_key:
                    quiz.provider_used = "gemini"
                    db.session.commit()
                    raw = _gemini_generate(prompt, gemini_key)
                elif provider == "deepseek" and deepseek_key:
                    quiz.provider_used = "deepseek"
                    db.session.commit()
                    raw = _deepseek_generate(prompt, deepseek_key)
                else:
                    raw = None
                    quiz.provider_used = f"{provider}-fallback"
                    db.session.commit()

                if raw:
                    parsed_rows = _extract_questions_lenient(raw)
                    if not parsed_rows:
                        batch_parse_failures += 1
                        parsed_rows = _fallback_questions(
                            quiz.field_of_study,
                            quiz.topic,
                            batch_total,
                            batch_mcq,
                            batch_tf,
                        )
                else:
                    parsed_rows = _fallback_questions(quiz.field_of_study, quiz.topic, batch_total, batch_mcq, batch_tf)

                normalized_rows = _normalize_questions(
                    parsed_rows,
                    batch_total,
                    batch_mcq,
                    batch_tf,
                    quiz.field_of_study,
                    quiz.topic,
                )
                aggregated_rows.extend(normalized_rows)
                quiz.generation_meta_json = json.dumps(
                    {
                        "batch_progress": f"{batch_index}/{total_batches}",
                        "generated_so_far": len(aggregated_rows),
                        "target_total": quiz.total_questions,
                        "parse_failures": batch_parse_failures,
                    }
                )
                db.session.commit()

            rows = _normalize_questions(
                aggregated_rows,
                quiz.total_questions,
                quiz.mcq_count,
                quiz.tf_count,
                quiz.field_of_study,
                quiz.topic,
            )

            # Replace previous generated set atomically.
            QuizOption.query.filter(
                QuizOption.question_id.in_(
                    db.session.query(QuizQuestion.id).filter_by(quiz_id=quiz.id)
                )
            ).delete(synchronize_session=False)
            QuizQuestion.query.filter_by(quiz_id=quiz.id).delete(synchronize_session=False)
            db.session.flush()

            order_idx = 1
            for row in rows:
                q = QuizQuestion(
                    quiz_id=quiz.id,
                    order_index=order_idx,
                    question_type=row["question_type"],
                    scenario=row.get("scenario") or "",
                    question_text=row.get("question_text") or "",
                    explanation=row.get("explanation") or "",
                    difficulty=row.get("difficulty") or "medium",
                    is_active=True,
                )
                db.session.add(q)
                db.session.flush()

                for opt in row.get("options", []):
                    db.session.add(
                        QuizOption(
                            question_id=q.id,
                            option_key=str(opt.get("key", "")).strip().upper(),
                            option_text=opt.get("text") or "",
                            is_correct=bool(opt.get("correct", False)),
                        )
                    )
                order_idx += 1

            quiz.status = "ready"
            quiz.generation_completed_at = datetime.utcnow()
            quiz.generation_meta_json = json.dumps(
                {
                    "generated_count": order_idx - 1,
                    "distribution": {"mcq": quiz.mcq_count, "true_false": quiz.tf_count},
                    "parse_failures": batch_parse_failures,
                }
            )
            if batch_parse_failures > 0:
                quiz.generation_error = (
                    f"{batch_parse_failures} batch(es) returned invalid JSON and were repaired with fallback questions."
                )
            db.session.commit()
        except Exception as exc:
            app.logger.exception("Quiz generation failed for quiz_id=%s", quiz.id)
            quiz.status = "draft"
            quiz.generation_error = f"AI generation failed. {str(exc)}"
            quiz.generation_completed_at = datetime.utcnow()
            db.session.commit()
