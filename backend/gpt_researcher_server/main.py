from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
import asyncio
import json
from typing import AsyncGenerator, Dict, Any
import logging
from gpt_researcher import GPTResearcher
import re

# Configure logging
logging.basicConfig( 
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

async def gpt_researcher_producer_gen(question: str) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Runs gpt-researcher and yields standardized updates.
    """
    thinking_log = ""
    final_report_content = ""
    is_reasoning = False

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
                researcher = GPTResearcher(query=question, report_type="deep", websocket=handler)
                logger.info("Starting research phase...")
                await researcher.conduct_research()
                logger.info("Research phase completed, starting report writing...")
                await researcher.write_report()
                logger.info("Report writing completed")
            except Exception as e:
                logger.error(f"Error during gpt-researcher execution: {e}", exc_info=True)
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
            # Replace any newlines and multiple spaces within a log message with a single space
            msg_output = msg_output_raw.strip()

            if msg_type == "logs":
                is_reasoning = True
                if msg_output:
                    thinking_log += f"{msg_output}\n\n"
                    logger.info(f"Added to thinking log: {msg_output[:100]}...")
            elif msg_type == "report":
                is_reasoning = False
                final_report_content += msg_output_raw
                logger.info(f"Added to final report: {msg_output_raw[:100]}...")
            elif msg_type == "error":
                logger.error(f"Received error from research task: {msg_output}")
                yield {"error": f"An error occurred: {msg_output}"}
                break

            yield {
                "think": thinking_log,
                "final": final_report_content,
                "is_reasoning": is_reasoning,
                "complete": False
            }

        await research_task
        logger.info("Research task completed, sending final state")
        # Signal completion with final state
        yield {
            "think": thinking_log,
            "final": final_report_content,
            "is_reasoning": False,
            "complete": True
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