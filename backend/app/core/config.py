import os


class Settings:
    """
    Central application settings.

    Values are read from environment variables where available so the
    same code can run in dev / staging / production without edits.
    In production, always set SECRET_KEY via the environment -
    the default below is ONLY for local development.
    """

    PROJECT_NAME: str = "Scientific Collaboration Network Analyzer"

    SECRET_KEY: str = os.getenv(
        "SCNA_SECRET_KEY", "dev-only-secret-change-me-in-production"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("SCNA_ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )


settings = Settings()
