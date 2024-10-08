import os.path
from typing import Optional
from os import environ, path
from dotenv import load_dotenv
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))

ENVIRONMENT = environ.get("ENVIRONMENT", "development")


class Settings(BaseSettings):
    PORT: int = 8081
    HOST: str = '0.0.0.0'
    URL: str = f"https://{HOST}:{PORT}"

    DB_PROVIDER_TYPE: str = environ.get("DB_PROVIDER_TYPE", "postgres")

    ALLOW_ORIGINS: str = ("*")
    ALLOW_CREDENTIALS: bool = True
    ALLOW_METHODS: str = ('*')
    ALLOW_HEADERS: str = ('*')

    # DB Settings
    __POSTGRESQL_HOST: str = environ.get("POSTGRESQL_HOST", "localhost")
    __POSTGRESQL_PORT: str = environ.get("POSTGRESQL_PORT", "5532")
    __POSTGRESQL_USER: str = environ.get("POSTGRESQL_USER", "postgres")
    __POSTGRESQL_PASSWORD: str = environ.get("POSTGRESQL_PASSWORD", "postgres")
    POSTGRESQL_DB: str = environ.get("POSTGRESQL_DATABASE", "postgres")
    REDIS_URL: str = environ.get("REDIS_URL", '')
    DATABASE_URL: str = f"postgresql://{__POSTGRESQL_USER}:{__POSTGRESQL_PASSWORD}@{__POSTGRESQL_HOST}:{__POSTGRESQL_PORT}/{POSTGRESQL_DB}"


settings = Settings()
