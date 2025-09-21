import os

from db_schema import DeepResearchAgent
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv("../../.env")  # Load from parent directory .env file
load_dotenv()  # Load from .env file and environment variables

DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_ENDPOINT = os.getenv("DB_ENDPOINT")
DB_PORT = 5432
DB_NAME = os.getenv("DB_NAME")

DB_URI = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_ENDPOINT}:{DB_PORT}/{DB_NAME}"


engine = create_engine(DB_URI, echo=True)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

deepreseach_systems = ["perplexity", "baseline", "gpt-researcher"]
deepresearch_system_names = [
    "Perplexity",
    "Simple Deepresearch (Gemini 2.5 Flash)",
    "GPT Researcher",
]

for i in range(len(deepreseach_systems)):
    new_entry = DeepResearchAgent(
        agent_id=deepreseach_systems[i], agent_name=deepresearch_system_names[i]
    )
    session.add(new_entry)
    session.commit()


all_rows = session.query(DeepResearchAgent).all()
for row in all_rows:
    print(row.__dict__)
session.close()
