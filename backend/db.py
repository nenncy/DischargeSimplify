# import os
# from dotenv import load_dotenv
# import psycopg2
# from psycopg2.extras import RealDictCursor  # gives you dict-like rows

# load_dotenv()

# def get_conn():
#     return psycopg2.connect(
#         dbname   = os.getenv("POSTGRES_DB"),
#         user     = os.getenv("POSTGRES_USER"),
#         password = os.getenv("POSTGRES_PASSWORD"),
#         host     = os.getenv("POSTGRES_HOST"),
#         port     = os.getenv("POSTGRES_PORT"),
#         cursor_factory=RealDictCursor
#     )

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Build the DATABASE_URL from your .env
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# SQLAlchemy engine + session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
