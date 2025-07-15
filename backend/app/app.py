from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import random 
import os
import uuid
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine,asc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID as pgUUID
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from dotenv import load_dotenv
from typing import  Dict, Any, AsyncGenerator
import json
import uvicorn
import logging
from db_schema import DeepResearchAgent, DeepResearchUserResponse, AnswerSpanVote, IntermediateStepVote, DeepresearchRankings
import httpx
import asyncio
import time


#Simple Deepresearch (Gemini 2.5 Flash) is referred to as baseline
# Configure logging
logging.basicConfig( 
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv('keys.env')


GPT_RESEARCHER_URL = os.getenv("GPT_RESEARCHER_URL")
PERPLEXITY_URL = os.getenv("PERPLEXITY_URL")
BASELINE_URL = os.getenv("BASELINE_URL")

DB_USERNAME = os.getenv("DB_USERNAME") 
DB_PASSWORD = os.getenv("DB_PASSWORD")
AWS_ENDPOINT = os.getenv("AWS_ENDPOINT")
DB_PORT = 5432
DB_NAME = os.getenv("DB_NAME")

DB_URI = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{AWS_ENDPOINT}:{DB_PORT}/{DB_NAME}?keepalives=1&keepalives_idle=30&keepalives_interval=10&keepalives_count=5"


engine = create_engine(DB_URI, echo = False,
    poolclass=QueuePool,
    pool_size=5,  # Number of connections to keep open
    max_overflow=10,  # Max extra connections when pool is full
    pool_timeout=30,  # Seconds to wait for a connection from pool
    pool_recycle=1800,  # Recycle connections after 30 minutes
    pool_pre_ping=True)

db_Session = sessionmaker(bind=engine)

@contextmanager
def get_session():
    session = db_Session()
    try:
        yield session
        session.commit()
    except:
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


def get_two_deep_research_agents():
    with get_session() as dbSession:
        rows = dbSession.query(DeepResearchAgent.agent_uuid).all()
    
    if len(rows) < 2:
        selected_rows = rows
    else:
        selected_rows = random.sample(rows, 2)
    
    selected_agents_dict = [{
        "id": str(row[0]) # Return UUID as a string
    } for row in selected_rows]

    logger.debug(f"Selected deep research agents: {selected_agents_dict}")
    return selected_agents_dict

def return_system_name(agent_id):
    with get_session() as dbSession:
        rows = dbSession.query(DeepResearchAgent.agent_name).filter(
        DeepResearchAgent.agent_id == agent_id
    ).all()
    assert len(rows) ==1
    return rows[0][0]

@app.get('/')
async def index():
    # This route previously used render_template, which is Flask-specific.
    # If serving an HTML file is needed, use FileResponse from fastapi.responses
    # from fastapi.responses import FileResponse
    # return FileResponse("path/to/your/index.html")
    # For now, returning a simple message or removing if not an API endpoint.
    return {"message": "Welcome to DeepResearch Comparator API. See /docs for API documentation."}


@app.get('/api/deepresearch-agents')
async def get_deep_research_agents_async():
    """Get available deep research agents."""
    selected_agents = get_two_deep_research_agents()
    session_id = str(uuid.uuid4())
    
    return JSONResponse({
        'status': 'success',
        'agents': selected_agents,
        'session_id': session_id
    })

async def streaming_service_producer_gen(url: str, service_name: str, question: str) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Generic producer for streaming services that return normalized responses.
    Calls the specified service URL and yields standardized updates.
    """
    try:
        async with httpx.AsyncClient(timeout=2000.0) as client:
            logger.info(f"Connecting to {service_name} service for question: {question}")
            async with client.stream("POST", url, json={"question": question}) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data_str = line[len("data:"):].strip()
                        if data_str:    
                            try:
                                data = json.loads(data_str)
                                yield data
                            except json.JSONDecodeError:
                                logger.error(f"Failed to decode json from {service_name} stream: '{data_str}'")
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
        result = db_session.query(DeepResearchAgent.agent_id).filter(DeepResearchAgent.agent_uuid == agent_uuid_obj).first()
    
    if result:
        return result[0]
    else:
        logger.warning(f"No agent found for UUID: {agent_uuid_str}")
        return None


async def agent_task_worker(
    agent_type: str, agent_id_str: str, question: str, q: asyncio.Queue
):
    """
    A worker that runs a producer generator and puts formatted results on the queue.
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

    # All services now return normalized responses, use the generic streaming producer
    producer = streaming_service_producer_gen(
        url=config["url"], 
        service_name=config["name"], 
        question=question
    )

    try:
        async for data in producer:
            payload = {}
            if "error" in data:
                payload[f"{agent_id_str}_final_report"] = data["error"]
                await q.put((agent_id_str, payload))
                break

            if data.get("intermediate_steps") is not None:
                payload[f"{agent_id_str}_intermediate_steps"] = data["intermediate_steps"]
            if data.get("final_report") is not None:
                payload[f"{agent_id_str}_final_report"] = data["final_report"]
            if data.get("is_intermediate") is not None:
                payload[f"{agent_id_str}_is_intermediate"] = data["is_intermediate"]
            if data.get("citations") is not None:
                payload[f"{agent_id_str}_citations"] = data["citations"]
            
            await q.put((agent_id_str, payload))
            
            if data.get("complete"):
                break # Producer signaled completion
    
    except Exception as e:
        logger.error(f"Unhandled error in agent_task_worker for {agent_id_str}: {e}", exc_info=True)
        error_payload = {f"{agent_id_str}_final": f"A critical error occurred: {e}"}
        await q.put((agent_id_str, error_payload))
    finally:
        await q.put((agent_id_str, None)) # Signal that this worker is done


@app.post('/api/deepresearch-question')
async def deep_research_question(request: Request):
    """
    Handles a deep research question by making calls to different agents based on request.
    Supports both streaming (Perplexity) and non-streaming (baseline) responses.
    """
    data = await request.json()
    question = data.get('question', "Tell me a fun fact about space.")
    selected_agents = data.get('selected_agents', {})
    
    if not selected_agents or not isinstance(selected_agents, dict) or 'agentA' not in selected_agents or 'agentB' not in selected_agents:
        raise HTTPException(status_code=400, detail="Selected agents data is required and must contain agentA and agentB")

    # The frontend now sends UUIDs. We need to look up the agent_id.
    agent_a_uuid = selected_agents.get('agentA')
    agent_b_uuid = selected_agents.get('agentB')

    agent_a_id = get_agent_id_from_uuid(agent_a_uuid)
    agent_b_id = get_agent_id_from_uuid(agent_b_uuid)

    if not agent_a_id or not agent_b_id:
        missing_agents = []
        if not agent_a_id: missing_agents.append(f"agentA (UUID: {agent_a_uuid})")
        if not agent_b_id: missing_agents.append(f"agentB (UUID: {agent_b_uuid})")
        raise HTTPException(status_code=404, detail=f"Could not find the following agent(s) in the database: {', '.join(missing_agents)}")


    q = asyncio.Queue()

    async def generate_agent_responses() -> AsyncGenerator[str, None]:
        logger.info(f"Starting deep research for question: '{question}' using agent A: {agent_a_id}, agent B: {agent_b_id}")

        initial_metadata = {
            "metadata": {"selected_agents": selected_agents, "agentA_id": agent_a_uuid, "agentB_id": agent_b_uuid},
            "agentA_intermediate_steps": None, "agentB_intermediate_steps": None,
            "agentA_final_report": None, "agentB_final_report": None,
            "agentA_is_intermediate": False, "agentB_is_intermediate": False,
            "agentA_is_complete": False, "agentB_is_complete": False,
            "agentA_citations": [], "agentB_citations": [],
            "agentA_updated": False, "agentB_updated": False, "final": False
        }
        yield json.dumps(initial_metadata) + "\n"
        
        # Create worker tasks for each agent
        task_a = asyncio.create_task(agent_task_worker(agent_a_id, "agentA", question, q))
        task_b = asyncio.create_task(agent_task_worker(agent_b_id, "agentB", question, q))
        tasks = [task_a, task_b]
        active_producers = len(tasks)

        combined_state = {
            "agentA_intermediate_steps": None, "agentB_intermediate_steps": None,
            "agentA_final_report": None, "agentB_final_report": None,
            "agentA_is_intermediate": False, "agentB_is_intermediate": False,
            "agentA_is_complete": False, "agentB_is_complete": False,
            "agentA_citations": [], "agentB_citations": [],
        }

        try:
            while active_producers > 0:
                try:
                    # Wait for an item from the queue, but with a timeout to allow for heartbeats
                    source_agent_id, chunk_data = await asyncio.wait_for(q.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    # If we time out, it means the agents are thinking. Send a heartbeat.
                    logger.debug("No agent output for 15s, sending heartbeat to keep connection alive.")
                    yield json.dumps({"heartbeat": True, "timestamp": time.time()}) + "\n"
                    continue

                q.task_done()

                if chunk_data is None:
                    active_producers -= 1
                    if source_agent_id == "agentA":
                        combined_state["agentA_is_complete"] = True
                    else:
                        combined_state["agentB_is_complete"] = True
                    
                    payload = combined_state.copy()
                    payload["agentA_updated"] = (source_agent_id == "agentA")
                    payload["agentB_updated"] = (source_agent_id == "agentB")
                    payload["final"] = (active_producers == 0)

                    yield json.dumps(payload) + "\n"
                    continue

                # Update combined state from the formatted chunk_data
                if "agentA_intermediate_steps" in chunk_data:
                    combined_state["agentA_intermediate_steps"] = chunk_data["agentA_intermediate_steps"]
                if "agentB_intermediate_steps" in chunk_data:
                    combined_state["agentB_intermediate_steps"] = chunk_data["agentB_intermediate_steps"]

                # If a final answer arrives, intermediate steps are over.
                if "agentA_final_report" in chunk_data:
                    combined_state["agentA_final_report"] = chunk_data["agentA_final_report"] 
                    combined_state["agentA_is_intermediate"] = False
                if "agentB_final_report" in chunk_data:
                    combined_state["agentB_final_report"] = chunk_data["agentB_final_report"]
                    combined_state["agentB_is_intermediate"] = False
                
                if "agentA_is_intermediate" in chunk_data:
                    combined_state["agentA_is_intermediate"] = chunk_data["agentA_is_intermediate"]
                if "agentB_is_intermediate" in chunk_data:
                    combined_state["agentB_is_intermediate"] = chunk_data["agentB_is_intermediate"]

                if "agentA_citations" in chunk_data:
                    combined_state["agentA_citations"] = chunk_data["agentA_citations"]
                    logger.info(f"Forwarding {len(chunk_data['agentA_citations'])} citations for agent A to frontend.")
                    logger.debug(f"agent A citations: {chunk_data['agentA_citations']}")
                if "agentB_citations" in chunk_data:
                    combined_state["agentB_citations"] = chunk_data["agentB_citations"]
                    logger.info(f"Forwarding {len(chunk_data['agentB_citations'])} citations for agent B to frontend.")
                    logger.debug(f"agent B citations: {chunk_data['agentB_citations']}")

                payload = combined_state.copy()
                payload["agentA_updated"] = (source_agent_id == "agentA")
                payload["agentB_updated"] = (source_agent_id == "agentB")
                payload["is_final"] = False
                
                yield json.dumps(payload) + "\n"

            # Final yield to ensure frontend knows both are complete.
            final_state = combined_state.copy()
            final_state["is_final"] = True
            final_state["agentA_is_complete"] = True
            final_state["agentA_is_complete"] = True
            final_state["agentA_updated"] = False
            final_state["agentB_updated"] = False
            yield json.dumps(final_state) + "\n"
        finally:
            logger.info("Cleaning up deep research tasks.")
            for task in tasks:
                if not task.done():
                    task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    return StreamingResponse(generate_agent_responses(), media_type='application/x-ndjson')


@app.post('/api/deepresearch-choice')
async def deep_research_choice(request: Request):
    """Process user's deep research agent choice and stores it in the database."""
    data = await request.json()
    if not data:
        raise HTTPException(status_code=400, detail="No data provided")
    
    choice = data.get('choice', '')
    question = data.get('question', '')
    conversation_a = data.get('conversation_a', [])
    conversation_b = data.get('conversation_b', [])
    selected_agents = data.get('selected_agents', [])
    session_id = data.get('session_id')
    
    # Ensure we have at least two agents to reference
    if not all([choice, conversation_a, conversation_b, selected_agents, len(selected_agents) >= 2, session_id]):
        raise HTTPException(status_code=400, detail="Missing required data")
    
    try:
        agent_a_uuid = selected_agents[0].get('id')
        agent_b_uuid = selected_agents[1].get('id')
        
        agent_a_id = get_agent_id_from_uuid(agent_a_uuid)
        agent_b_id = get_agent_id_from_uuid(agent_b_uuid)

        if not agent_a_id or not agent_b_id:
            missing_agents = []
            if not agent_a_id: missing_agents.append(f"agentA (UUID: {agent_a_uuid})")
            if not agent_b_id: missing_agents.append(f"agentB (UUID: {agent_b_uuid})")
            raise HTTPException(status_code=404, detail=f"Could not find the following agent(s) in the database: {', '.join(missing_agents)}")

        # Generate the UUID before creating the database object
        response_id = str(uuid.uuid4())
        
        new_response = DeepResearchUserResponse(
            id=response_id,
            session_id=session_id,
            agentid_a=agent_a_id,
            agentid_b=agent_b_id,
            question = question,
            conversation_a=json.dumps(conversation_a),
            conversation_b=json.dumps(conversation_b),
            userresponse=choice
        )
        
        with get_session() as dbSession:
            dbSession.add(new_response)
        
        # Use the local variable `response_id` for logging to avoid accessing the detached instance
        logger.info(f"Stored deep research choice. ID: {response_id}")
        agent_a_name = return_system_name(agent_a_id)
        agent_b_name = return_system_name(agent_b_id)
        logger.debug(f"Agent a name : {agent_a_name}")
        logger.debug(f"Agent b name : {agent_b_name}")

        return JSONResponse({
            'status': 'success',
            'message': 'Choice recorded successfully.',
            'AgentA': {
                'name': agent_a_name
            },
            'AgentB': {
                'name': agent_b_name
            }
        })

    except Exception as e:
        logger.error(f"Failed to process deep research choice: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to record choice.")


@app.post('/api/answer-span-vote')
async def answer_span_vote(request: Request):
    """Logs a user's vote on a specific span of text in the answer_span_votes table."""
    data = await request.json()
    
    # Extract data from the request
    vote = data.get('vote') # 'up' or 'down'
    highlighted_text = data.get('highlighted_text')
    agent_uuid = data.get('agent_uuid') 
    session_id = data.get('session_id')

    if not all([vote, highlighted_text, agent_uuid, session_id]):
        raise HTTPException(status_code=400, detail="Missing required fields for vote.")

    agent_id = get_agent_id_from_uuid(agent_uuid)
    if not agent_id:
        raise HTTPException(status_code=404, detail=f"agent with UUID '{agent_uuid}' not found.")

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

    return JSONResponse(content={"status": "success", "message": "Vote recorded"}, status_code=200)


@app.post('/api/intermediate-step-vote')
async def intermediate_step_vote(request: Request):
    """Logs a user's vote on a specific intermediate step."""
    data = await request.json()
    
    # Extract data from the request
    vote = data.get('vote')  # 'up' or 'down'
    step_text = data.get('step_text')
    agent_uuid = data.get('agent_uuid')
    session_id = data.get('session_id')

    if not all([vote, step_text, agent_uuid, session_id]):
        raise HTTPException(status_code=400, detail="Missing required fields for vote.")

    agent_id = get_agent_id_from_uuid(agent_uuid)
    if not agent_id:
        raise HTTPException(status_code=404, detail=f"agent with UUID '{agent_uuid}' not found.")

    try:
        with get_session() as db_session:
            new_vote = IntermediateStepVote(
                session_id=session_id,
                agent_id=agent_id,
                vote=vote,
                intermediate_step=step_text,
            )
            db_session.add(new_vote)
        
        logger.info(f"Stored intermediate step vote for agent_id: {agent_id}, vote: {vote}.")

    except Exception as e:
        logger.error(f"Failed to write intermediate step vote to database: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to record intermediate step vote.")

    return JSONResponse(content={"status": "success", "message": "Vote recorded"}, status_code=200)



@app.get('/api/ranking')
async def ranking_async():   
    with get_session() as dbSession:
        rows = dbSession.query(DeepresearchRankings.SYSTEMID).filter(
            DeepresearchRankings.ISLATEST == True
        ).order_by(asc(DeepresearchRankings.RANK)).all()
        rows_serial_number = []
        for i in range(len(rows)):
            rows_ranking = (
                dbSession.query(
                    DeepresearchRankings.RANK,
                    DeepresearchRankings.SYSTEMNAME,
                    DeepresearchRankings.ARENASCORE,
                    DeepresearchRankings.VOTES, 
                    DeepresearchRankings.STEPUPVOTE_RATE, 
                    DeepresearchRankings.TEXTUPVOTE_RATE
                )
                .filter(
                    DeepresearchRankings.SYSTEMID == rows[i][0],
                    DeepresearchRankings.ISLATEST == True
                )
                .all()
            )
            assert len(rows_ranking)==1
            rows_serial_number.append(rows_ranking[0])
    
        return JSONResponse({
            'status': 'success',
            'ranking': [
                {
                    'rank': item[0],
                    'systemname': item[1],
                    'score': item[2], 
                    'votes': item[3],
                    'stepupvote': item[4],
                    'textupvote': item[5]
                } for item in rows_serial_number
            ]
        })

if __name__ == '__main__':
    # To run with uvicorn: uvicorn app_cw:app --host 0.0.0.0 --port 5001 --reload
    uvicorn.run("app:app", host='0.0.0.0', port=5001, reload=True)