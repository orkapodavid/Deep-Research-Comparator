import sqlalchemy
import uuid
from sqlalchemy import  Column, String,Text, Integer, Float , Boolean
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID as pgUUID

Base = declarative_base()

class DeepresearchRankings(Base):
     __tablename__ = 'deepresearch_rankings'
          
     ID = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
     SYSTEMID  =  Column(String(65535)) # same as agent_id from DeepResearchAgent
     SYSTEMNAME =  Column(String(65535)) 
     VOTES = Column(Integer)
     RANK =  Column(Integer)
     ARENASCORE = Column(Float)
     STEPUPVOTE_RATE = Column(Float)
     TEXTUPVOTE_RATE = Column(Float)
     ISLATEST = Column(Boolean)
     LASTUPDATED =Column(sqlalchemy.TIMESTAMP, server_default=func.now())

class DeepResearchAgent(Base):
    __tablename__ = 'deepresearch_agents'
    agent_uuid = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(64), nullable=False, unique=True)
    agent_name = Column(Text)

class DeepResearchUserResponse(Base):
    __tablename__ = 'deepresearch_user_response'
    id = Column(String(128), primary_key=True)
    session_id = Column(pgUUID(as_uuid=True),nullable=False, unique = True)
    agentid_a = Column(String(128))
    agentid_b = Column(String(128))
    question = Column(String(65535))
    conversation_a = Column(Text)
    conversation_b = Column(Text)
    userresponse = Column(String(128))
    lastupdated = Column(sqlalchemy.TIMESTAMP, server_default=func.now())

class AnswerSpanVote(Base):
    __tablename__ = 'answer_span_votes'
    id = Column(pgUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    session_id = Column(pgUUID(as_uuid=True), nullable=False)
    timestamp = Column(sqlalchemy.TIMESTAMP, server_default=func.now())
    agent_id = Column(String(128), nullable=False)
    vote = Column(String(10), nullable=False)
    highlighted_text = Column(Text, nullable=False)

class IntermediateStepVote(Base):
    __tablename__ = 'intermediate_step_votes'
    id = Column(pgUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    session_id = Column(pgUUID(as_uuid=True), nullable=False)
    timestamp = Column(sqlalchemy.TIMESTAMP, server_default=func.now())
    agent_id = Column(String(128), nullable=False)
    vote = Column(String(10), nullable=False)
    intermediate_step = Column(Text, nullable=False)