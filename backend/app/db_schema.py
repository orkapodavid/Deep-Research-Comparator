import uuid

import sqlalchemy
from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class DeepResearchAgent(Base):
    __tablename__ = "deepresearch_agents"
    agent_uuid = Column(pgUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(64), nullable=False, unique=True)
    agent_name = Column(Text)


class DeepResearchUserResponse(Base):
    __tablename__ = "deepresearch_user_response"
    id = Column(String(128), primary_key=True)
    session_id = Column(pgUUID(as_uuid=True), nullable=False, unique=True)
    agentid_a = Column(String(128))
    agentid_b = Column(String(128))
    question = Column(String(65535))
    conversation_a = Column(Text)
    conversation_b = Column(Text)
    userresponse = Column(String(128))
    lastupdated = Column(sqlalchemy.TIMESTAMP, server_default=func.now())


class AnswerSpanVote(Base):
    __tablename__ = "answer_span_votes"
    id = Column(
        pgUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    session_id = Column(pgUUID(as_uuid=True), nullable=False)
    timestamp = Column(sqlalchemy.TIMESTAMP, server_default=func.now())
    agent_id = Column(String(128), nullable=False)
    vote = Column(String(10), nullable=False)
    highlighted_text = Column(Text, nullable=False)


class IntermediateStepVote(Base):
    __tablename__ = "intermediate_step_votes"
    id = Column(
        pgUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    session_id = Column(pgUUID(as_uuid=True), nullable=False)
    timestamp = Column(sqlalchemy.TIMESTAMP, server_default=func.now())
    agent_id = Column(String(128), nullable=False)
    vote = Column(String(10), nullable=False)
    intermediate_step = Column(Text, nullable=False)


class ConversationHistory(Base):
    __tablename__ = "conversation_history"
    id = Column(
        pgUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    session_id = Column(pgUUID(as_uuid=True), nullable=False)
    timestamp = Column(sqlalchemy.TIMESTAMP, server_default=func.now())
    question = Column(Text, nullable=False)
    agent_a_id = Column(String(128), nullable=False)  # agent_id like 'perplexity'
    agent_a_name = Column(String(255), nullable=False)  # human readable name
    agent_a_response = Column(Text, nullable=False)
    agent_a_intermediate_steps = Column(Text)
    agent_a_citations = Column(Text)  # JSON string of citations
    agent_b_id = Column(String(128), nullable=False)
    agent_b_name = Column(String(255), nullable=False)
    agent_b_response = Column(Text, nullable=False)
    agent_b_intermediate_steps = Column(Text)
    agent_b_citations = Column(Text)  # JSON string of citations
    agent_c_id = Column(String(128), nullable=False)
    agent_c_name = Column(String(255), nullable=False)
    agent_c_response = Column(Text, nullable=False)
    agent_c_intermediate_steps = Column(Text)
    agent_c_citations = Column(Text)  # JSON string of citations
