from itsdangerous import URLSafeTimedSerializer

from app.config import settings

_serializer = URLSafeTimedSerializer(settings.token_secret_key)


def generate_unsubscribe_token(email: str) -> str:
    return _serializer.dumps(email, salt="unsubscribe")


def verify_unsubscribe_token(token: str, max_age_seconds: int = 60 * 60 * 24 * 30) -> str:
    return _serializer.loads(token, salt="unsubscribe", max_age=max_age_seconds)