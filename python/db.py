"""
db.py - one place that builds the database connection, so the other scripts
do not each repeat it.

It reads MYSQL_USER, MYSQL_PASSWORD and MYSQL_HOST from the .env file in the
project folder. (If you set DB_URL, for example to a test database, that is
used instead.)
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine

PROJECT_DIR = Path(__file__).resolve().parent.parent


def get_engine():
    url = os.environ.get("DB_URL")
    if url:
        return create_engine(url)
    load_dotenv(PROJECT_DIR / ".env")
    return create_engine(
        f"mysql+pymysql://{os.environ['MYSQL_USER']}:{os.environ['MYSQL_PASSWORD']}"
        f"@{os.environ.get('MYSQL_HOST', 'localhost')}/hotel_bookings"
    )
