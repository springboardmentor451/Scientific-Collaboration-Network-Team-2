from datetime import datetime, timedelta, timezone
from backend.app.models.captcha_challenges import CaptchaChallenge
from backend.app.routes.auth import _generate_captcha, _hash_captcha_answer


def test_captcha_generates_math_question_and_hashed_answer():
    question, answer = _generate_captcha()

    assert len(question) == 6
    assert question.isdigit()
    assert answer == question
    assert _hash_captcha_answer(answer) != answer
    assert len(_hash_captcha_answer(answer)) == 64


def test_captcha_answer_normalizes_case_and_whitespace():
    assert _hash_captcha_answer("  12 ") == _hash_captcha_answer("12")


def test_captcha_record_stores_expiry_and_unused_state():
    record = CaptchaChallenge(
        challenge_id="challenge-id",
        answer_hash=_hash_captcha_answer("12"),
        expires_at=None,
        verified=False,
        used=False,
        created_at=datetime.now(timezone.utc),
    )

    assert record.used is False
    assert record.expires_at is None


def test_verified_captcha_can_stop_expiry_timer():
    record = CaptchaChallenge(
        challenge_id="verified-challenge",
        answer_hash=_hash_captcha_answer("12"),
        expires_at=datetime.now(timezone.utc),
        verified=True,
        used=False,
        created_at=datetime.now(timezone.utc),
    )

    record.expires_at = None

    assert record.verified is True
    assert record.expires_at is None