from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os


load_dotenv()


DATABASE_URL = os.getenv(
    "DATABASE_URL"
)


if not DATABASE_URL:

    raise ValueError(
        "DATABASE_URL is not configured in .env"
    )


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


def ensure_captcha_schema():
    with engine.begin() as connection:
        connection.execute(text(
            "ALTER TABLE captcha_challenges "
            "ADD COLUMN IF NOT EXISTS verified BOOLEAN NOT NULL DEFAULT FALSE"
        ))
        connection.execute(text(
            "ALTER TABLE captcha_challenges "
            "ALTER COLUMN expires_at DROP NOT NULL"
        ))


def ensure_profile_schema():
    with engine.begin() as connection:
        connection.execute(text(
            "ALTER TABLE users "
            "ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500)"
        ))


def test_connection():

    try:

        with engine.connect() as connection:

            connection.execute(
                text("SELECT 1")
            )

        return True

    except Exception as error:

        print(
            "Database connection error:",
            error
        )

        return False