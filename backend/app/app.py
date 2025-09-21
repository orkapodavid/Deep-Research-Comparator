import asyncio
import json
import logging
import os
import secrets
import time
import uuid
from contextlib import contextmanager
from typing import Any, AsyncGenerator, Dict

import httpx
import uvicorn
from db_schema import (
    AnswerSpanVote,
    ConversationHistory,
    DeepResearchAgent,
    DeepResearchUserResponse,
    IntermediateStepVote,
)
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# Simple Deepresearch (Gemini 2.5 Flash) is referred to as baseline

# Authentication configuration
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "password")

security = HTTPBasic()


def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    """Simple username/password authentication."""
    is_correct_username = secrets.compare_digest(credentials.username, AUTH_USERNAME)
    is_correct_password = secrets.compare_digest(credentials.password, AUTH_PASSWORD)

    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables from parent directory
load_dotenv("../../.env")  # Load from parent directory .env file
load_dotenv()  # Also load from current directory and environment variables


GPT_RESEARCHER_URL = os.getenv("GPT_RESEARCHER_URL")
PERPLEXITY_URL = os.getenv("PERPLEXITY_URL")
BASELINE_URL = os.getenv("BASELINE_URL")

DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_ENDPOINT = os.getenv("DB_ENDPOINT")
DB_PORT = 5432
DB_NAME = os.getenv("DB_NAME")

# Log environment variable status
print("=== Main App Environment Variables ===")
print(f"GPT_RESEARCHER_URL: {'✓ SET' if GPT_RESEARCHER_URL else '✗ NOT SET'}")
print(f"PERPLEXITY_URL: {'✓ SET' if PERPLEXITY_URL else '✗ NOT SET'}")
print(f"BASELINE_URL: {'✓ SET' if BASELINE_URL else '✗ NOT SET'}")
print(f"DB_USERNAME: {'✓ SET' if DB_USERNAME else '✗ NOT SET'}")
print(f"DB_PASSWORD: {'✓ SET' if DB_PASSWORD else '✗ NOT SET'}")
print(f"DB_ENDPOINT: {'✓ SET' if DB_ENDPOINT else '✗ NOT SET'}")
print(f"DB_NAME: {'✓ SET' if DB_NAME else '✗ NOT SET'}")
print("======================================")

DB_URI = (
    f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_ENDPOINT}:"
    f"{DB_PORT}/{DB_NAME}?keepalives=1&keepalives_idle=30"
    f"&keepalives_interval=10&keepalives_count=5"
)


engine = create_engine(
    DB_URI,
    echo=False,
    poolclass=QueuePool,
    pool_size=5,  # Number of connections to keep open
    max_overflow=10,  # Max extra connections when pool is full
    pool_timeout=30,  # Seconds to wait for a connection from pool
    pool_recycle=1800,  # Recycle connections after 30 minutes
    pool_pre_ping=True,
)

db_Session = sessionmaker(bind=engine)


@contextmanager
def get_session():
    session = db_Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


Base = declarative_base()


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}


def get_all_deep_research_agents():
    """Get all available deep research agents with their names."""
    with get_session() as dbSession:
        rows = dbSession.query(
            DeepResearchAgent.agent_uuid,
            DeepResearchAgent.agent_id,
            DeepResearchAgent.agent_name,
        ).all()

    selected_agents_dict = [
        {
            "id": str(row[0]),  # UUID as string
            "agent_id": row[1],  # agent_id (perplexity, baseline, etc.)
            "name": row[2],  # human-readable name
        }
        for row in rows
    ]

    logger.debug(f"Available deep research agents: {selected_agents_dict}")
    return selected_agents_dict


def return_system_name(agent_id):
    with get_session() as dbSession:
        rows = (
            dbSession.query(DeepResearchAgent.agent_name)
            .filter(DeepResearchAgent.agent_id == agent_id)
            .all()
        )
    assert len(rows) == 1
    return rows[0][0]


@app.get("/")
async def index():
    # This route previously used render_template, which is Flask-specific.
    # If serving an HTML file is needed, use FileResponse from
    # fastapi.responses
    # from fastapi.responses import FileResponse
    # return FileResponse("path/to/your/index.html")
    # For now, returning a simple message or removing if not an API endpoint.
    return {
        "message": (
            "Welcome to DeepResearch Comparator API. "
            "See /docs for API documentation."
        )
    }


@app.get("/api/deepresearch-agents")
async def get_deep_research_agents_async():
    """Get all available deep research agents."""
    all_agents = get_all_deep_research_agents()
    session_id = str(uuid.uuid4())

    return JSONResponse(
        {"status": "success", "agents": all_agents, "session_id": session_id}
    )


async def streaming_service_producer_gen(
    url: str, service_name: str, question: str
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Generic producer for streaming services that return normalized responses.
    Calls the specified service URL and yields standardized updates.
    """
    try:
        async with httpx.AsyncClient(timeout=2000.0) as client:
            logger.info(
                f"Connecting to {service_name} service for question: " f"{question}"
            )
            async with client.stream(
                "POST", url, json={"question": question}
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data_str = line[len("data:") :].strip()
                        if data_str:
                            try:
                                data = json.loads(data_str)
                                yield data
                            except json.JSONDecodeError:
                                logger.error(
                                    f"Failed to decode json from "
                                    f"{service_name} stream: '{data_str}'"
                                )
    except Exception as e:
        error_msg = f"Error in {service_name} service producer: {e}"
        logger.error(error_msg, exc_info=True)
        yield {"error": error_msg}


def get_agent_id_from_uuid(agent_uuid_str: str) -> str:
    """Fetches a agent's string ID from its UUID."""
    if not agent_uuid_str:
        return None
    try:
        agent_uuid_obj = uuid.UUID(agent_uuid_str)
    except (ValueError, TypeError):
        logger.error(f"Invalid UUID provided: {agent_uuid_str}")
        return None

    with get_session() as db_session:
        result = (
            db_session.query(DeepResearchAgent.agent_id)
            .filter(DeepResearchAgent.agent_uuid == agent_uuid_obj)
            .first()
        )

    if result:
        return result[0]
    else:
        logger.warning(f"No agent found for UUID: {agent_uuid_str}")
        return None


async def agent_task_worker(
    agent_type: str, agent_id_str: str, question: str, q: asyncio.Queue
):
    """
    A worker that runs a producer generator and puts formatted results on
    the queue.
    """
    # Map agent types to their service URLs and names
    service_config = {
        "perplexity": {"url": PERPLEXITY_URL, "name": "perplexity"},
        "baseline": {"url": BASELINE_URL, "name": "baseline"},
        "gpt-researcher": {"url": GPT_RESEARCHER_URL, "name": "gpt-researcher"},
    }

    config = service_config.get(agent_type)
    if not config:
        error_payload = {f"{agent_id_str}_final": f"Unknown agent type: {agent_type}"}
        await q.put((agent_id_str, error_payload))
        await q.put((agent_id_str, None))
        return

    # All services now return normalized responses, use the generic
    # streaming producer
    producer = streaming_service_producer_gen(
        url=config["url"], service_name=config["name"], question=question
    )

    try:
        async for data in producer:
            payload = {}
            if "error" in data:
                payload[f"{agent_id_str}_final_report"] = data["error"]
                await q.put((agent_id_str, payload))
                break

            if data.get("intermediate_steps") is not None:
                payload[f"{agent_id_str}_intermediate_steps"] = data[
                    "intermediate_steps"
                ]
            if data.get("final_report") is not None:
                payload[f"{agent_id_str}_final_report"] = data["final_report"]
            if data.get("is_intermediate") is not None:
                payload[f"{agent_id_str}_is_intermediate"] = data["is_intermediate"]
            if data.get("citations") is not None:
                payload[f"{agent_id_str}_citations"] = data["citations"]

            await q.put((agent_id_str, payload))

            if data.get("complete"):
                break  # Producer signaled completion

    except Exception as e:
        logger.error(
            f"Unhandled error in agent_task_worker for {agent_id_str}: {e}",
            exc_info=True,
        )
        error_payload = {f"{agent_id_str}_final": f"A critical error occurred: {e}"}
        await q.put((agent_id_str, error_payload))
    finally:
        await q.put((agent_id_str, None))  # Signal that this worker is done


@app.post("/api/deepresearch-question")
async def deep_research_question(
    request: Request, username: str = Depends(authenticate)
):
    """
    Handles a deep research question by making calls to all three agents.
    Supports both streaming (Perplexity) and non-streaming (baseline)
    responses.
    """
    data = await request.json()
    question = data.get("question", "Tell me a fun fact about space.")

    # Get all available agents
    all_agents = get_all_deep_research_agents()

    if len(all_agents) < 3:
        raise HTTPException(
            status_code=400,
            detail="Not enough agents available. Need at least 3 agents.",
        )

    q = asyncio.Queue()

    async def generate_agent_responses() -> AsyncGenerator[str, None]:
        logger.info(
            f"Starting deep research for question: '{question}' using all "
            f"available agents: {[agent['agent_id'] for agent in all_agents]}"
        )

        initial_metadata = {
            "metadata": {
                "all_agents": all_agents,
            },
            "agentA_intermediate_steps": None,
            "agentB_intermediate_steps": None,
            "agentC_intermediate_steps": None,
            "agentA_final_report": None,
            "agentB_final_report": None,
            "agentC_final_report": None,
            "agentA_is_intermediate": False,
            "agentB_is_intermediate": False,
            "agentC_is_intermediate": False,
            "agentA_is_complete": False,
            "agentB_is_complete": False,
            "agentC_is_complete": False,
            "agentA_citations": [],
            "agentB_citations": [],
            "agentC_citations": [],
            "agentA_updated": False,
            "agentB_updated": False,
            "agentC_updated": False,
            "final": False,
        }
        yield json.dumps(initial_metadata) + "\n"

        # Create worker tasks for each agent
        tasks = []
        agent_labels = ["agentA", "agentB", "agentC"]

        for i, agent in enumerate(all_agents[:3]):
            task = asyncio.create_task(
                agent_task_worker(agent["agent_id"], agent_labels[i], question, q)
            )
            tasks.append(task)

        active_producers = len(tasks)

        combined_state = {
            "agentA_intermediate_steps": None,
            "agentB_intermediate_steps": None,
            "agentC_intermediate_steps": None,
            "agentA_final_report": None,
            "agentB_final_report": None,
            "agentC_final_report": None,
            "agentA_is_intermediate": False,
            "agentB_is_intermediate": False,
            "agentC_is_intermediate": False,
            "agentA_is_complete": False,
            "agentB_is_complete": False,
            "agentC_is_complete": False,
            "agentA_citations": [],
            "agentB_citations": [],
            "agentC_citations": [],
        }

        try:
            while active_producers > 0:
                try:
                    # Wait for an item from the queue, but with a timeout
                    source_agent_id, chunk_data = await asyncio.wait_for(
                        q.get(), timeout=15.0
                    )
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    logger.debug("No agent output for 15s, sending heartbeat.")
                    yield json.dumps(
                        {"heartbeat": True, "timestamp": time.time()}
                    ) + "\n"
                    continue

                q.task_done()

                if chunk_data is None:
                    active_producers -= 1
                    if source_agent_id == "agentA":
                        combined_state["agentA_is_complete"] = True
                    elif source_agent_id == "agentB":
                        combined_state["agentB_is_complete"] = True
                    elif source_agent_id == "agentC":
                        combined_state["agentC_is_complete"] = True

                    payload = combined_state.copy()
                    payload["agentA_updated"] = source_agent_id == "agentA"
                    payload["agentB_updated"] = source_agent_id == "agentB"
                    payload["agentC_updated"] = source_agent_id == "agentC"
                    payload["final"] = active_producers == 0

                    yield json.dumps(payload) + "\n"
                    continue

                # Update combined state from chunk_data
                for step_key in [
                    "agentA_intermediate_steps",
                    "agentB_intermediate_steps",
                    "agentC_intermediate_steps",
                ]:
                    if step_key in chunk_data:
                        combined_state[step_key] = chunk_data[step_key]

                for report_key in [
                    "agentA_final_report",
                    "agentB_final_report",
                    "agentC_final_report",
                ]:
                    if report_key in chunk_data:
                        combined_state[report_key] = chunk_data[report_key]
                        # Mark as no longer intermediate when final report arrives
                        agent_prefix = report_key.split("_")[0]
                        combined_state[f"{agent_prefix}_is_intermediate"] = False

                for intermediate_key in [
                    "agentA_is_intermediate",
                    "agentB_is_intermediate",
                    "agentC_is_intermediate",
                ]:
                    if intermediate_key in chunk_data:
                        combined_state[intermediate_key] = chunk_data[intermediate_key]

                for citation_key in [
                    "agentA_citations",
                    "agentB_citations",
                    "agentC_citations",
                ]:
                    if citation_key in chunk_data:
                        combined_state[citation_key] = chunk_data[citation_key]
                        agent_letter = citation_key.split("_")[0][-1]  # Get A, B, or C
                        logger.info(
                            f"Forwarding {len(chunk_data[citation_key])} citations for agent {agent_letter}."
                        )

                payload = combined_state.copy()
                payload["agentA_updated"] = source_agent_id == "agentA"
                payload["agentB_updated"] = source_agent_id == "agentB"
                payload["agentC_updated"] = source_agent_id == "agentC"
                payload["is_final"] = False

                yield json.dumps(payload) + "\n"

            # Final yield to ensure frontend knows all are complete
            final_state = combined_state.copy()
            final_state["is_final"] = True
            final_state["agentA_is_complete"] = True
            final_state["agentB_is_complete"] = True
            final_state["agentC_is_complete"] = True
            final_state["agentA_updated"] = False
            final_state["agentB_updated"] = False
            final_state["agentC_updated"] = False
            yield json.dumps(final_state) + "\n"
        finally:
            logger.info("Cleaning up deep research tasks.")
            for task in tasks:
                if not task.done():
                    task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    return StreamingResponse(
        generate_agent_responses(), media_type="application/x-ndjson"
    )


@app.post("/api/deepresearch-choice")
async def deep_research_choice(request: Request):
    """Process user's deep research agent choice and stores it in the database."""
    data = await request.json()
    if not data:
        raise HTTPException(status_code=400, detail="No data provided")

    choice = data.get("choice", "")
    question = data.get("question", "")
    conversation_a = data.get("conversation_a", [])
    conversation_b = data.get("conversation_b", [])
    selected_agents = data.get("selected_agents", [])
    session_id = data.get("session_id")

    # Ensure we have at least two agents to reference
    if not all(
        [
            choice,
            conversation_a,
            conversation_b,
            selected_agents,
            len(selected_agents) >= 2,
            session_id,
        ]
    ):
        raise HTTPException(status_code=400, detail="Missing required data")

    try:
        agent_a_uuid = selected_agents[0].get("id")
        agent_b_uuid = selected_agents[1].get("id")

        agent_a_id = get_agent_id_from_uuid(agent_a_uuid)
        agent_b_id = get_agent_id_from_uuid(agent_b_uuid)

        if not agent_a_id or not agent_b_id:
            missing_agents = []
            if not agent_a_id:
                missing_agents.append(f"agentA (UUID: {agent_a_uuid})")
            if not agent_b_id:
                missing_agents.append(f"agentB (UUID: {agent_b_uuid})")
            raise HTTPException(
                status_code=404,
                detail=f"Could not find the following agent(s) in the database: {
                    ', '.join(missing_agents)}",
            )

        # Generate the UUID before creating the database object
        response_id = str(uuid.uuid4())

        new_response = DeepResearchUserResponse(
            id=response_id,
            session_id=session_id,
            agentid_a=agent_a_id,
            agentid_b=agent_b_id,
            question=question,
            conversation_a=json.dumps(conversation_a),
            conversation_b=json.dumps(conversation_b),
            userresponse=choice,
        )

        with get_session() as dbSession:
            dbSession.add(new_response)

        # Use the local variable `response_id` for logging to avoid accessing the
        # detached instance
        logger.info(f"Stored deep research choice. ID: {response_id}")
        agent_a_name = return_system_name(agent_a_id)
        agent_b_name = return_system_name(agent_b_id)
        logger.debug(f"Agent a name : {agent_a_name}")
        logger.debug(f"Agent b name : {agent_b_name}")

        return JSONResponse(
            {
                "status": "success",
                "message": "Choice recorded successfully.",
                "AgentA": {"name": agent_a_name},
                "AgentB": {"name": agent_b_name},
            }
        )

    except Exception as e:
        logger.error(f"Failed to process deep research choice: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to record choice.")


@app.post("/api/answer-span-vote")
async def answer_span_vote(request: Request):
    """Logs a user's vote on a specific span of text in the answer_span_votes table."""
    data = await request.json()

    # Extract data from the request
    vote = data.get("vote")  # 'up' or 'down'
    highlighted_text = data.get("highlighted_text")
    agent_uuid = data.get("agent_uuid")
    session_id = data.get("session_id")

    if not all([vote, highlighted_text, agent_uuid, session_id]):
        raise HTTPException(status_code=400, detail="Missing required fields for vote.")

    agent_id = get_agent_id_from_uuid(agent_uuid)
    if not agent_id:
        raise HTTPException(
            status_code=404, detail=f"agent with UUID '{agent_uuid}' not found."
        )

    try:
        with get_session() as db_session:
            new_vote = AnswerSpanVote(
                session_id=session_id,
                agent_id=agent_id,
                vote=vote,
                highlighted_text=highlighted_text,
            )
            db_session.add(new_vote)

        logger.info(f"Stored answer span vote for agent_id: {agent_id}, vote: {vote}.")

    except Exception as e:
        logger.error(f"Failed to write span vote to database: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to record span vote.")

    return JSONResponse(
        content={"status": "success", "message": "Vote recorded"}, status_code=200
    )


@app.post("/api/intermediate-step-vote")
async def intermediate_step_vote(request: Request):
    """Logs a user's vote on a specific intermediate step."""
    data = await request.json()

    # Extract data from the request
    vote = data.get("vote")  # 'up' or 'down'
    step_text = data.get("step_text")
    agent_uuid = data.get("agent_uuid")
    session_id = data.get("session_id")

    if not all([vote, step_text, agent_uuid, session_id]):
        raise HTTPException(status_code=400, detail="Missing required fields for vote.")

    agent_id = get_agent_id_from_uuid(agent_uuid)
    if not agent_id:
        raise HTTPException(
            status_code=404, detail=f"agent with UUID '{agent_uuid}' not found."
        )

    try:
        with get_session() as db_session:
            new_vote = IntermediateStepVote(
                session_id=session_id,
                agent_id=agent_id,
                vote=vote,
                intermediate_step=step_text,
            )
            db_session.add(new_vote)

        logger.info(
            f"Stored intermediate step vote for agent_id: {agent_id}, vote: {vote}."
        )

    except Exception as e:
        logger.error(
            f"Failed to write intermediate step vote to database: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="Failed to record intermediate step vote."
        )

    return JSONResponse(
        content={"status": "success", "message": "Vote recorded"}, status_code=200
    )


@app.post("/api/save-conversation")
async def save_conversation(request: Request, username: str = Depends(authenticate)):
    """
    Save a complete conversation with all three agents to the database.
    """
    data = await request.json()

    required_fields = [
        "session_id",
        "question",
        "agent_a_id",
        "agent_a_name",
        "agent_a_response",
        "agent_b_id",
        "agent_b_name",
        "agent_b_response",
        "agent_c_id",
        "agent_c_name",
        "agent_c_response",
    ]

    for field in required_fields:
        if field not in data:
            raise HTTPException(
                status_code=400, detail=f"Missing required field: {field}"
            )

    try:
        with get_session() as db_session:
            conversation = ConversationHistory(
                session_id=data["session_id"],
                question=data["question"],
                agent_a_id=data["agent_a_id"],
                agent_a_name=data["agent_a_name"],
                agent_a_response=data["agent_a_response"],
                agent_a_intermediate_steps=data.get("agent_a_intermediate_steps"),
                agent_a_citations=data.get("agent_a_citations"),
                agent_b_id=data["agent_b_id"],
                agent_b_name=data["agent_b_name"],
                agent_b_response=data["agent_b_response"],
                agent_b_intermediate_steps=data.get("agent_b_intermediate_steps"),
                agent_b_citations=data.get("agent_b_citations"),
                agent_c_id=data["agent_c_id"],
                agent_c_name=data["agent_c_name"],
                agent_c_response=data["agent_c_response"],
                agent_c_intermediate_steps=data.get("agent_c_intermediate_steps"),
                agent_c_citations=data.get("agent_c_citations"),
            )
            db_session.add(conversation)

        logger.info(f"Saved conversation for session {data['session_id']}")
        return JSONResponse(
            {"status": "success", "message": "Conversation saved successfully"}
        )

    except Exception as e:
        logger.error(f"Error saving conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save conversation")


@app.get("/api/conversation-history")
async def get_conversation_history(
    page: int = 1, page_size: int = 10, username: str = Depends(authenticate)
):
    """
    Get paginated conversation history.
    """
    offset = (page - 1) * page_size

    try:
        with get_session() as db_session:
            conversations = (
                db_session.query(ConversationHistory)
                .order_by(ConversationHistory.timestamp.desc())
                .offset(offset)
                .limit(page_size)
                .all()
            )

            total_count = db_session.query(ConversationHistory).count()

            result = []
            for conv in conversations:
                result.append(
                    {
                        "id": str(conv.id),
                        "session_id": str(conv.session_id),
                        "timestamp": conv.timestamp.isoformat(),
                        "question": conv.question,
                        "agents": [
                            {
                                "id": conv.agent_a_id,
                                "name": conv.agent_a_name,
                                "response": conv.agent_a_response,
                                "intermediate_steps": conv.agent_a_intermediate_steps,
                                "citations": conv.agent_a_citations,
                            },
                            {
                                "id": conv.agent_b_id,
                                "name": conv.agent_b_name,
                                "response": conv.agent_b_response,
                                "intermediate_steps": conv.agent_b_intermediate_steps,
                                "citations": conv.agent_b_citations,
                            },
                            {
                                "id": conv.agent_c_id,
                                "name": conv.agent_c_name,
                                "response": conv.agent_c_response,
                                "intermediate_steps": conv.agent_c_intermediate_steps,
                                "citations": conv.agent_c_citations,
                            },
                        ],
                    }
                )

            return JSONResponse(
                {
                    "status": "success",
                    "conversations": result,
                    "pagination": {
                        "page": page,
                        "page_size": page_size,
                        "total_count": total_count,
                        "total_pages": (total_count + page_size - 1) // page_size,
                    },
                }
            )

    except Exception as e:
        logger.error(f"Error retrieving conversation history: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve conversation history"
        )


@app.get("/api/conversation/{conversation_id}")
async def get_conversation_by_id(conversation_id: str):
    """
    Get a specific conversation by ID.
    """
    try:
        conversation_uuid = uuid.UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid conversation ID format")

    try:
        with get_session() as db_session:
            conversation = (
                db_session.query(ConversationHistory)
                .filter(ConversationHistory.id == conversation_uuid)
                .first()
            )

            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")

            result = {
                "id": str(conversation.id),
                "session_id": str(conversation.session_id),
                "timestamp": conversation.timestamp.isoformat(),
                "question": conversation.question,
                "agents": [
                    {
                        "id": conversation.agent_a_id,
                        "name": conversation.agent_a_name,
                        "response": conversation.agent_a_response,
                        "intermediate_steps": conversation.agent_a_intermediate_steps,
                        "citations": conversation.agent_a_citations,
                    },
                    {
                        "id": conversation.agent_b_id,
                        "name": conversation.agent_b_name,
                        "response": conversation.agent_b_response,
                        "intermediate_steps": conversation.agent_b_intermediate_steps,
                        "citations": conversation.agent_b_citations,
                    },
                    {
                        "id": conversation.agent_c_id,
                        "name": conversation.agent_c_name,
                        "response": conversation.agent_c_response,
                        "intermediate_steps": conversation.agent_c_intermediate_steps,
                        "citations": conversation.agent_c_citations,
                    },
                ],
            }

            return JSONResponse({"status": "success", "conversation": result})

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve conversation")


if __name__ == "__main__":
    # To run with uvicorn: uvicorn app_cw:app --host 0.0.0.0 --port 5001 --reload
    uvicorn.run("app:app", host="0.0.0.0", port=5001, reload=True)
