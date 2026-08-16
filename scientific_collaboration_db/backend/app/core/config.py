# """
# Centralized application configuration.

# Values are read from environment variables / a local .env file.
# See .env.example for the full list of supported settings.
# """
# from functools import lru_cache

# from pydantic_settings import BaseSettings, SettingsConfigDict


# class Settings(BaseSettings):
#     model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

#     APP_ENV: str = "development"
#     SECRET_KEY: str = "change-this-secret-key-in-production"
#     JWT_ALGORITHM: str = "HS256"
#     ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours
#     EMAIL_VERIFICATION_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

#     # Public base URL of this API, used to build the verification link sent by email
#     API_BASE_URL: str = "http://localhost:8000"

#     # SMTP (used to send real verification emails). Leave SMTP_USERNAME blank
#     # to fall back to "dev mode", where the verification link is logged to the
#     # console / returned in the API response instead of emailed.
#     SMTP_HOST: str = "smtp.gmail.com"
#     SMTP_PORT: int = 587
#     SMTP_USE_TLS: bool = True
#     SMTP_USERNAME: str = ""
#     SMTP_PASSWORD: str = ""
#     SMTP_FROM_EMAIL: str = ""
#     # SMTP_FROM_NAME: str = "Scientific Collaboration Network Analyzer"

#     SMTP_FROM_NAME: str = "Scientific Collaboration Network Analyzer"

#     # 2-step verification code lifetime
#     LOGIN_OTP_EXPIRE_MINUTES: int = 10

#     # "Sign in with Google" — create an OAuth 2.0 Client ID (type: Web
#     # application) at https://console.cloud.google.com/apis/credentials
#     # and put it here. Leave blank to disable the Google sign-in endpoint.
#     GOOGLE_CLIENT_ID: str = ""

# # -----

#     POSTGRES_USER: str = "scan_user"
#     POSTGRES_PASSWORD: str = "scan_password"
#     POSTGRES_DB: str = "scientific_collab_db"
#     POSTGRES_HOST: str = "localhost"
#     POSTGRES_PORT: int = 5432

#     DATABASE_URL: str | None = None

#     @property
#     def sqlalchemy_database_url(self) -> str:
#         if self.DATABASE_URL:
#             return self.DATABASE_URL
#         return (
#             f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
#             f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
#         )


# @lru_cache
# def get_settings() -> Settings:
#     return Settings()


"""
Centralized application configuration.

Values are read from environment variables / a local .env file.
See .env.example for the full list of supported settings.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_ENV: str = "development"
    SECRET_KEY: str = "change-this-secret-key-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours
    EMAIL_VERIFICATION_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Public base URL of this API, used to build the verification link sent by email
    API_BASE_URL: str = "http://localhost:8000"

    # SMTP (used to send real verification emails). Leave SMTP_USERNAME blank
    # to fall back to "dev mode", where the verification link is logged to the
    # console / returned in the API response instead of emailed.
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USE_TLS: bool = True
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "Scientific Collaboration Network Analyzer"

    # 2-step verification code lifetime
    LOGIN_OTP_EXPIRE_MINUTES: int = 10

    # "Sign in with Google" — create an OAuth 2.0 Client ID (type: Web
    # application) at https://console.cloud.google.com/apis/credentials
    # and put it here. Leave blank to disable the Google sign-in endpoint.
    GOOGLE_CLIENT_ID: str = ""

    POSTGRES_USER: str = "scan_user"
    POSTGRES_PASSWORD: str = "scan_password"
    POSTGRES_DB: str = "scientific_collab_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    DATABASE_URL: str | None = None

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()