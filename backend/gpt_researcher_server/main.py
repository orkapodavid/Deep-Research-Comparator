import asyncio
import json
import logging
import os
from typing import Any, AsyncGenerator, Dict

import openai
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from gpt_researcher import GPTResearcher

# Load environment variables from parent directory
load_dotenv("../../.env")  # Load from parent directory .env file
load_dotenv()  # Also load from current directory and environment variables

# Log environment variable status
print("=== GPT Researcher Server Environment Variables ===")
openai_api_key = os.getenv("OPENAI_API_KEY")
serper_api_key = os.getenv("SERPER_API_KEY")
print(f"OPENAI_API_KEY: {'✓ SET' if openai_api_key else '✗ NOT SET'}")
print(f"SERPER_API_KEY: {'✓ SET' if serper_api_key else '✗ NOT SET'}")

# Set GPT Researcher specific environment variables
os.environ["RETRIEVER"] = "serper"  # Use Serper as the search engine
os.environ["FAST_LLM"] = "openai:gpt-4o-mini"  # Use a valid OpenAI model
os.environ["SMART_LLM"] = "openai:gpt-4o"  # Use a valid OpenAI model
os.environ["STRATEGIC_LLM"] = "openai:gpt-4o"  # Use a valid OpenAI model
os.environ["EMBEDDING"] = "openai:text-embedding-3-small"  # Use a valid embedding model

print(f"RETRIEVER: {os.getenv('RETRIEVER')}")
print(f"FAST_LLM: {os.getenv('FAST_LLM')}")
print(f"SMART_LLM: {os.getenv('SMART_LLM')}")
print(f"STRATEGIC_LLM: {os.getenv('STRATEGIC_LLM')}")
print(f"EMBEDDING: {os.getenv('EMBEDDING')}")
print("====================================================")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/health")
async def health_check():
    """Health check endpoint that also validates configuration"""
    health_status = {"status": "ok", "service": "gpt-researcher"}

    # Check if required environment variables are set
    missing_vars = []
    if not os.getenv("OPENAI_API_KEY"):
        missing_vars.append("OPENAI_API_KEY")
    if not os.getenv("SERPER_API_KEY"):
        missing_vars.append("SERPER_API_KEY")

    if missing_vars:
        health_status["status"] = "degraded"
        health_status["missing_env_vars"] = missing_vars
        health_status["message"] = "Some required environment variables are missing"

    health_status["configuration"] = {
        "retriever": os.getenv("RETRIEVER", "serper"),
        "fast_llm": os.getenv("FAST_LLM", "openai:gpt-4o-mini"),
        "smart_llm": os.getenv("SMART_LLM", "openai:gpt-4o"),
        "strategic_llm": os.getenv("STRATEGIC_LLM", "openai:gpt-4o"),
        "embedding": os.getenv("EMBEDDING", "openai:text-embedding-3-small"),
    }

    return health_status


@app.get("/test-connections")
async def test_api_connections():
    """
    Test endpoint to verify OpenAI and Serper API connections
    """
    results = {
        "openai": {"status": "unknown", "message": ""},
        "serper": {"status": "unknown", "message": ""},
        "overall_status": "unknown",
    }

    # Test OpenAI API
    try:
        if not os.getenv("OPENAI_API_KEY"):
            results["openai"]["status"] = "error"
            results["openai"]["message"] = "OPENAI_API_KEY not set"
        else:
            # Test OpenAI with a simple request
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": "Say 'Hello' if you can read this."}
                ],
                max_tokens=10,
            )

            if response and response.choices:
                results["openai"]["status"] = "success"
                results["openai"]["message"] = "Connected successfully"
            else:
                results["openai"]["status"] = "error"
                results["openai"]["message"] = "No response from OpenAI API"

    except Exception as e:
        results["openai"]["status"] = "error"
        results["openai"]["message"] = f"Error: {str(e)}"

    # Test Serper API
    try:
        if not os.getenv("SERPER_API_KEY"):
            results["serper"]["status"] = "error"
            results["serper"]["message"] = "SERPER_API_KEY not set"
        else:
            # Test Serper with a simple search
            url = "https://google.serper.dev/search"
            payload = {"q": "test search", "num": 1}
            headers = {
                "X-API-KEY": os.getenv("SERPER_API_KEY"),
                "Content-Type": "application/json",
            }

            response = requests.post(url, headers=headers, json=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if "organic" in data and len(data["organic"]) > 0:
                    results["serper"]["status"] = "success"
                    results["serper"][
                        "message"
                    ] = f"Connected successfully, found {len(data['organic'])} results"
                else:
                    results["serper"]["status"] = "warning"
                    results["serper"]["message"] = "Connected but no results returned"
            else:
                results["serper"]["status"] = "error"
                results["serper"][
                    "message"
                ] = f"HTTP {response.status_code}: {response.text[:100]}"

    except Exception as e:
        results["serper"]["status"] = "error"
        results["serper"]["message"] = f"Error: {str(e)}"

    # Determine overall status
    if results["openai"]["status"] == "success" and results["serper"]["status"] in [
        "success",
        "warning",
    ]:
        results["overall_status"] = "success"
    elif results["openai"]["status"] == "success" or results["serper"]["status"] in [
        "success",
        "warning",
    ]:
        results["overall_status"] = "partial"
    else:
        results["overall_status"] = "error"

    return results


async def gpt_researcher_producer_gen(
    question: str,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Runs gpt-researcher and yields standardized updates.
    """
    intermediate_steps = ""
    final_report_content = ""
    is_intermediate = False

    try:
        # 1. Define a custom handler to capture structured messages from gpt-researcher
        local_message_q = asyncio.Queue()

        class CustomStreamingHandler:
            def __init__(self, queue: asyncio.Queue):
                self.queue = queue

            async def send_json(self, data: dict):
                await self.queue.put(data)

        handler = CustomStreamingHandler(local_message_q)

        async def run_research():
            try:
                # Validate API keys before starting research
                if not os.getenv("OPENAI_API_KEY"):
                    raise ValueError(
                        "OPENAI_API_KEY is not set. Please configure your OpenAI API key."
                    )
                if not os.getenv("SERPER_API_KEY"):
                    raise ValueError(
                        "SERPER_API_KEY is not set. Please configure your Serper API key."
                    )

                researcher = GPTResearcher(
                    query=question, report_type="research_report", websocket=handler
                )
                logger.info("Starting research phase...")
                await researcher.conduct_research()
                logger.info("Research phase completed, starting report writing...")
                await researcher.write_report()
                logger.info("Report writing completed")
            except Exception as e:
                logger.error(
                    f"Error during gpt-researcher execution: {e}", exc_info=True
                )
                await local_message_q.put({"type": "error", "output": str(e)})
            finally:
                await local_message_q.put(None)

        research_task = asyncio.create_task(run_research())

        while True:
            message = await local_message_q.get()
            if message is None:
                logger.info("Received completion signal from research task")
                break

            msg_type = message.get("type")
            msg_output_raw = message.get("output", "")
            # Replace any newlines and multiple spaces within a log message with a
            # single space
            msg_output = msg_output_raw.strip() if msg_output_raw else ""

            if msg_type == "logs":
                is_intermediate = True
                if msg_output:
                    intermediate_steps += f"{msg_output}|||---|||"
                    logger.info(f"Added to thinking log: {msg_output[:100]}...")
            elif msg_type == "report":
                is_intermediate = False
                final_report_content += msg_output_raw if msg_output_raw else ""
                logger.info(
                    f"Added to final report: {msg_output_raw[:100] if msg_output_raw else 'Empty report'}..."
                )
            elif msg_type == "error":
                logger.error(f"Received error from research task: {msg_output}")
                yield {"error": f"An error occurred: {msg_output}"}
                break
            elif msg_type == "path":
                # Handle path messages (sources/references)
                logger.info(
                    f"Processing source: {msg_output[:100] if msg_output else 'Unknown source'}..."
                )
                continue  # Don't yield for path messages, just log them

            # Only yield if we have meaningful content
            if intermediate_steps or final_report_content:
                yield {
                    "intermediate_steps": intermediate_steps,
                    "final_report": final_report_content,
                    "is_intermediate": is_intermediate,
                    "is_complete": False,  # citations are not present for GPT researcher
                }

        await research_task
        logger.info("Research task completed, sending final state")
        # Signal completion with final state
        yield {
            "intermediate_steps": intermediate_steps,
            "final_report": final_report_content,
            "is_intermediate": False,
            "is_complete": True,
        }

    except Exception as e:
        error_msg = f"Error in gpt_researcher_producer_gen: {e}"
        logger.error(error_msg, exc_info=True)
        yield {"error": error_msg}


@app.post("/run")
async def run_gpt_researcher(request: Request):
    data = await request.json()
    question = data.get("question")

    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")

    async def stream_generator():
        async for result in gpt_researcher_producer_gen(question):
            yield f"data: {json.dumps(result)}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=5004, reload=True)
