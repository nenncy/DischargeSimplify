import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor  # gives you dict-like rows

load_dotenv()

def get_conn():
    return psycopg2.connect(
        dbname   = os.getenv("POSTGRES_DB"),
        user     = os.getenv("POSTGRES_USER"),
        password = os.getenv("POSTGRES_PASSWORD"),
        host     = os.getenv("POSTGRES_HOST"),
        port     = os.getenv("POSTGRES_PORT"),
        cursor_factory=RealDictCursor
    )