import httpx
import json
import os
import logging
import asyncio

logger = logging.getLogger(__name__)
from dotenv import load_dotenv
load_dotenv('keys.env')
# It's recommended to set PERPLEXITY_API_KEY in your environment variables
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
# You can also add PPLX_MODEL_NAME to your environment variables, or default it here
DEFAULT_PPLX_MODEL_NAME = os.getenv("PPLX_MODEL_NAME", "sonar-deep-research")

async def stream_perplexity_api(model: str | None = None, user_message: str = "", system_message: str | None = None):
    """
    Asynchronously streams responses from the Perplexity API.
    Yields content chunks (str) from the stream for successful data.
    Yields a JSON string representing an error object if an error occurs.
    """
    if not PERPLEXITY_API_KEY:
        logger.error("PERPLEXITY_API_KEY not found in environment variables.")
        # Yield a JSON string indicating error
        yield json.dumps({"error": "Perplexity API key not configured.", "model_name": model or DEFAULT_PPLX_MODEL_NAME})
        return

    actual_model = model or DEFAULT_PPLX_MODEL_NAME
    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }

    messages = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    if not user_message:
        logger.warning(f"User message is empty for Perplexity API call to model {actual_model}.")
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": actual_model,
        "messages": messages,
        "stream": True
    }

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream("POST", url, headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line and line.startswith('data: '):
                        event_data = line[len('data: '):].strip()
                        if event_data == '[DONE]':
                            break
                        try:
                            data = json.loads(event_data)
                            chunk_data = {}
                            # Extract content delta
                            if data.get('choices') and len(data['choices']) > 0:
                                delta = data['choices'][0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    chunk_data['content'] = content
                            
                            # Extract citations if they exist in the chunk
                            if 'citations' in data:
                                chunk_data['citations'] = data['citations']

                            if chunk_data:
                                yield chunk_data # Yield a dictionary of findings
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to decode JSON from Perplexity stream: {event_data}")
                            continue # Skip malformed lines
                        except Exception as e:
                            logger.error(f"Error processing chunk from Perplexity for model {actual_model}: {e}, data: {event_data}")
                            # Yield an error structure if a specific chunk fails mid-stream
                            yield {"error": f"Chunk processing error: {str(e)}", "model_name": actual_model, "original_chunk": event_data}
                            continue
    except httpx.HTTPStatusError as e:
        error_body_bytes = await e.response.aread()
        error_detail = error_body_bytes.decode(errors='replace')
        logger.error(f"Perplexity API request failed for model {actual_model} with status {e.response.status_code}: {error_detail}")
        yield json.dumps({"error": f"Perplexity API error ({e.response.status_code})", "detail": error_detail, "model_name": actual_model})
    except httpx.RequestError as e:
        logger.error(f"RequestError connecting to Perplexity API for model {actual_model}: {e}")
        yield json.dumps({"error": f"Network error connecting to Perplexity API: {str(e)}", "model_name": actual_model})
    except Exception as e:
        logger.exception(f"Unexpected error in stream_perplexity_api for model {actual_model}:") # Logs with stack trace
        yield json.dumps({"error": f"Unexpected error streaming from Perplexity: {type(e).__name__} - {str(e)}", "model_name": actual_model}) 