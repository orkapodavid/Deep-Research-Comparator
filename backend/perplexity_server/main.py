import json
import logging
import os
import re
from typing import Any, AsyncGenerator, Dict

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from perplexity_client import stream_perplexity_api

# Load environment variables from parent directory
load_dotenv("../../.env")  # Load from parent directory .env file
load_dotenv()  # Also load from current directory and environment variables

# Log environment variable status
perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
print("=== Perplexity Server Environment Variables ===")
print(f"PERPLEXITY_API_KEY: {'✓ SET' if perplexity_api_key else '✗ NOT SET'}")
print("===============================================")

# Use direct import to get the client

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.get("/test-connections")
async def test_api_connections():
    """
    Test endpoint to verify Perplexity API connection
    """
    results = {
        "perplexity": {"status": "unknown", "message": ""},
        "overall_status": "unknown",
    }

    # Test Perplexity API
    try:
        if not os.getenv("PERPLEXITY_API_KEY"):
            results["perplexity"]["status"] = "error"
            results["perplexity"]["message"] = "PERPLEXITY_API_KEY not set"
        else:
            # Test Perplexity with a simple request
            url = "https://api.perplexity.ai/chat/completions"
            payload = {
                "model": "sonar",
                "messages": [
                    {"role": "user", "content": "Say 'Hello' if you can read this."}
                ],
                "max_tokens": 10,
                "stream": False,
            }
            headers = {
                "Authorization": f"Bearer {os.getenv('PERPLEXITY_API_KEY')}",
                "Content-Type": "application/json",
            }

            response = requests.post(url, headers=headers, json=payload, timeout=15)

            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    results["perplexity"]["status"] = "success"
                    results["perplexity"]["message"] = "Connected successfully"
                else:
                    results["perplexity"]["status"] = "warning"
                    results["perplexity"][
                        "message"
                    ] = "Connected but no response content"
            else:
                results["perplexity"]["status"] = "error"
                results["perplexity"][
                    "message"
                ] = f"HTTP {response.status_code}: {response.text[:100]}"

    except Exception as e:
        results["perplexity"]["status"] = "error"
        results["perplexity"]["message"] = f"Error: {str(e)}"

    # Set overall status
    results["overall_status"] = results["perplexity"]["status"]

    return results


def fix_markdown(text: str) -> str:
    # 1. Ensure space after header hashes. Corrects "##Header" to "## Header".
    text = re.sub(r"(#+)([A-Za-z])", r"\1 \2", text)

    # 2. Ensure newlines before headers. Corrects "Text## Header" to
    # "Text\n\n## Header".
    text = re.sub(r"([^\n])(\s*#+\s)", r"\1\n\n\2", text)

    # 3. Clean up stray 's' characters on a new line, likely from
    # pluralization artifacts.
    text = re.sub(r"([a-zA-Z])\ns\n", r"\1s\n\n", text)

    # 4. Normalize various broken horizontal rule artifacts into a clean one.
    text = text.replace(".--\n-", "\n\n---\n\n")
    text = text.replace("--\n-", "\n\n---\n\n")

    # 5. Collapse multiple consecutive horizontal rules into a single one.
    text = re.sub(r"(\n\s*---\s*\n)+", "\n\n---\n\n", text)

    # 6. Attempt to fix broken markdown table separators.
    text = re.sub(r"(\|\s*-{3,}\s*)\n(\s*-{3,}\s*\|)", r"\1|\2", text)

    # 7. Add a newline before list items that are stuck to text.
    text = re.sub(r"([^\n])(\n\s*[-*] )", r"\1\n\2", text)

    return text.strip()


async def perplexity_producer_gen(
    question: str,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Streams from Perplexity API and yields standardized updates.
    """
    current_intermediate_content = ""
    current_final_content = ""
    all_citations = []  # Master list of all citations found so far
    in_intermediate_block = False
    try:
        async for chunk_data in stream_perplexity_api(user_message=question):
            # Check if the chunk is an error JSON
            if isinstance(chunk_data, dict) and "error" in chunk_data:
                logger.error(f"Received error from Perplexity client: {chunk_data}")
                yield {"error": chunk_data.get("detail", "Unknown perplexity error")}
                return

            content_chunk = chunk_data.get("content", "")

            # Process content based on whether we are inside a <think> block
            if in_intermediate_block:
                if "</think>" in content_chunk:
                    # End of think block found
                    intermediate_part, final_part = content_chunk.split("</think>", 1)
                    current_intermediate_content += intermediate_part
                    current_final_content += final_part
                    in_intermediate_block = False
                else:
                    # Still in think block
                    current_intermediate_content += content_chunk
            elif "<think>" in content_chunk:
                # Start of think block found
                final_part, intermediate_part = content_chunk.split("<think>", 1)
                current_final_content += final_part
                in_intermediate_block = True

                # Check if the think block also ends in this same chunk
                if "</think>" in intermediate_part:
                    intermediate_part_actual, final_part_after = (
                        intermediate_part.split("</think>", 1)
                    )
                    current_intermediate_content += intermediate_part_actual
                    current_final_content += final_part_after
                    in_intermediate_block = False
                else:
                    current_intermediate_content += intermediate_part
            else:
                # Not in a think block, and no think block starts
                current_final_content += content_chunk

            current_intermediate_content = current_intermediate_content.replace(
                "\n\n", "|||---|||"
            ).strip()
            # This is the base payload for this chunk
            payload = {
                "intermediate_steps": current_intermediate_content,
                "final_report": fix_markdown(current_final_content),
                "is_intermediate": in_intermediate_block,
                "complete": False,
            }

            # Only add citations to the payload if the list has changed
            if "citations" in chunk_data:
                if chunk_data["citations"] != all_citations:
                    all_citations = chunk_data["citations"]
                    payload["citations"] = all_citations

            yield payload

    except Exception as e:
        error_msg = f"Error in perplexity_producer_gen: {e}"
        logger.error(error_msg, exc_info=True)
        yield {"error": error_msg}
    finally:
        # Send a final completion message with all data to ensure consistency
        yield {
            "intermediate_steps": current_intermediate_content,
            "final_report": fix_markdown(current_final_content),
            "is_intermediate": False,
            "is_complete": True,
            "citations": all_citations,
        }


@app.post("/run")
async def run_perplexity(request: Request):
    data = await request.json()
    question = data.get("question")

    if not question:
        raise HTTPException(status_code=400, detail="Question is required.")

    async def stream_generator():
        async for result in perplexity_producer_gen(question):
            yield f"data: {json.dumps(result)}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    # Note: The port is different from the gpt-researcher service
    uvicorn.run("main:app", host="0.0.0.0", port=5005, reload=True)
