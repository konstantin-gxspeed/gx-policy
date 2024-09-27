# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.engine.url import make_url

def create_database_if_not_exists(url):
    url_object = make_url(url)
    if not database_exists(url_object):
        create_database(url_object)

create_database_if_not_exists(settings.DATABASE_URL)
engine = create_engine( settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()