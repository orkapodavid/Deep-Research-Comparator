import os
from sqlalchemy import  create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

from db_schema import DeepResearchAgent, DeepResearchUserResponse, AnswerSpanVote,IntermediateStepVote , DeepresearchRankings 

load_dotenv('keys.env')

DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
AWS_ENDPOINT = os.getenv("AWS_ENDPOINT")
DB_PORT = 5432
DB_NAME = os.getenv("DB_NAME")

DB_URI = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{AWS_ENDPOINT}:{DB_PORT}/{DB_NAME}"
print(DB_URI)
engine = create_engine(DB_URI, echo = False)

Base = declarative_base()

DeepResearchAgent.__table__.create(bind=engine)
DeepResearchUserResponse.__table__.create(bind=engine)
AnswerSpanVote.__table__.create(bind=engine)
IntermediateStepVote.__table__.create(bind=engine)
DeepresearchRankings.__table__.create(bind=engine)




md = MetaData()
md.reflect(bind=engine)  

print("The tables are")
print(md.tables.keys())