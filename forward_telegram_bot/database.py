import os

from dotenv import load_dotenv
from sqlmodel import create_engine

load_dotenv()


db = create_engine(os.environ['DATABASE_URI'])
