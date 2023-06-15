import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

load_dotenv()


db = create_engine(os.environ['DATABASE_URI'])
session = Session(db)
