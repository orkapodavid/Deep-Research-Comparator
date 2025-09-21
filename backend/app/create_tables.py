import os

from db_schema import (
    AnswerSpanVote,
    ConversationHistory,
    DeepResearchAgent,
    DeepResearchUserResponse,
    IntermediateStepVote,
)
from dotenv import load_dotenv
from sqlalchemy import MetaData, create_engine
from sqlalchemy.ext.declarative import declarative_base

load_dotenv("../../.env")  # Load from parent directory .env file
load_dotenv()  # Load from .env file and environment variables

DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_ENDPOINT = os.getenv("DB_ENDPOINT")
DB_PORT = 5432
DB_NAME = os.getenv("DB_NAME")

DB_URI = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_ENDPOINT}:{DB_PORT}/{DB_NAME}"
print(DB_URI)
engine = create_engine(DB_URI, echo=False)

Base = declarative_base()

DeepResearchAgent.__table__.create(bind=engine, checkfirst=True)
DeepResearchUserResponse.__table__.create(bind=engine, checkfirst=True)
AnswerSpanVote.__table__.create(bind=engine, checkfirst=True)
IntermediateStepVote.__table__.create(bind=engine, checkfirst=True)
ConversationHistory.__table__.create(bind=engine, checkfirst=True)


md = MetaData()
md.reflect(bind=engine)

print("The tables are")
print(md.tables.keys())
