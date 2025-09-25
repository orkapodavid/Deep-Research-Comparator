"""
Arguments:
    --query: research question
    --long_report: generate long report (default is short answer)
    --answer_path: output file path for the answer
    --log_dir: log directory

Logs:
- see all system messages in /logs
    - /logs/search.log: search query and results
    - /logs/observation.log: observation of the environment
    - /logs/input.log: input to the model at each turn
    - /logs/response.log: response (after format check)
    - /logs/trajectory.md: total trajectory of the agent

"""

import json
import os
import re
import traceback

import google.generativeai as generativeai
import openai
import requests
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from google import genai
from google.genai import types
from prompt import report_format_reminder_prompt, report_prompt, summary_reminder_prompt
from retrieval import query_clueweb, query_serper

app = Flask(__name__)
CORS(
    app,
    origins="*",
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
)


# Load environment variables from parent directory
load_dotenv("../../.env")  # Load from parent directory .env file
load_dotenv()  # Also load from current directory and environment variables

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PROJECT_ID = "[deepresearch-llm-modeling]"
LOCATION = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")
MODEL_ID = "gemini-2.5-pro-preview-05-06"
MODEL_ID_Flash = "gemini-2.5-flash-preview-05-20"

# Log environment variable status
print("=== Simple DeepResearch Server Environment Variables ===")
print(f"GEMINI_API_KEY: {'✓ SET' if GEMINI_API_KEY else '✗ NOT SET'}")
print(f"SERPER_API_KEY: {'✓ SET' if SERPER_API_KEY else '✗ NOT SET'}")
print(f"OPENAI_API_KEY: {'✓ SET' if OPENAI_API_KEY else '✗ NOT SET'}")
print(f"PERPLEXITY_API_KEY: {'✓ SET' if PERPLEXITY_API_KEY else '✗ NOT SET'}")
print(
    f"GOOGLE_CLOUD_REGION: {'✓ SET' if LOCATION != 'us-central1' else '✓ DEFAULT (us-central1)'}"
)
print("=========================================================")

ACTIONS = ["search", "answer", "plan", "scripts", "summary"]


generativeai.configure(api_key=GEMINI_API_KEY)

MAX_CONTEXT_LENGTH = 40000


class LLMAgent:
    def __init__(self, config, is_flash: bool = True):
        if is_flash:
            self.model_name = MODEL_ID_Flash
        else:
            self.model_name = MODEL_ID
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.consecutive_search_cnt = (
            0  # number of consecutive search actions performed for each sample
        )
        self.search_cnt = 0  # number of total search actions performed for each sample
        self.script_cnt = 0
        self.summary_cnt = 0  # number of total context length in each turn
        self.num_env_steps = 0
        self.summary_history = ""
        self.config = config
        self.context_cnt = []
        self.current_think_content = ""

    def run_llm_loop(self, prompt):
        done = False
        input = prompt

        for step in range(self.config["max_turns"]):
            try:
                self.num_env_steps += 1

                print(f"=====turn {self.num_env_steps}======")

                # start = time.time()
                thought, action = self.query_gemini(input)
                actioname, content = self.parse_action(action)

                if actioname == "scripts" or actioname == "summary":
                    content = self.remove_markdown_blocks(content)

                response_with_thought = f"<think>{thought}</think>\n\n{action}"

                # self._record_trajectory(input, response_with_thought)

                # execute actions (search or answer) and get observations
                done, updated_history, next_obs = self.execute_response(
                    action, self.config["num_docs"]
                )
                # end = time.time()

                step_intermediate = f"### Step {self.num_env_steps}\n"

                if thought and thought != "None":
                    step_intermediate += f"""**Thought**

1. {thought}

"""

                if actioname == "plan" and content != "None":
                    step_intermediate += f"""

**ACTION: Plan**

1. {content}"""

                if actioname == "search" and next_obs != "None":
                    step_intermediate += f"""

**ACTION: Search**

1. {next_obs}"""

                if actioname == "scripts" and content != "None":
                    step_intermediate += f"""

**ACTION: Scripts**

1. {content}"""

                if actioname == "summary" and content != "None":
                    step_intermediate += f"""

**ACTION: Summary**

1. {content}"""

                self.current_think_content += step_intermediate + "|||---|||"

                # Yield normalized format
                yield {
                    "intermediate_steps": self.current_think_content,
                    "final_report": None,
                    "is_intermediate": True,
                    "is_complete": False,
                }
                # print(f"Time taken for step {self.num_env_steps} is {end-start}")
                if done:
                    print("=====final response======")
                    break

                input = self._update_input(
                    input, response_with_thought, next_obs, updated_history, prompt
                )
            except Exception as e:
                print(f"Error: {e}")
                print(traceback.format_exc())
                exit()

        answer = self._compose_final_output(action)
        yield {
            "intermediate_steps": None,
            "final_report": answer,
            "is_intermediate": False,
            "is_complete": True,
        }

    def query_gemini(self, prompt):
        # TODO: consider how to deal with a response without any action.
        """Query Gemini with action format check. Only return the response with correct format.
        Args:
            prompt: prompt
        Returns:
            response_with_thought: response with correct format and thought process
        """
        try_time = 0

        while try_time < self.config["max_try_time"]:
            try_time += 1

            # Initialize variables
            thought = ""
            original_response = ""

            try:
                gemini_response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(include_thoughts=True)
                    ),
                )

                for part in gemini_response.candidates[0].content.parts:
                    if not part.text:
                        continue
                    if part.thought:
                        thought = part.text
                    else:
                        original_response = part.text

            except Exception as e:
                print(f"Error: {e}")
                continue
            # print("Original Response")
            # print(original_response)
            action = self.postprocess_response(original_response)

            if action is None:
                print("response with wrong format!")

                # add format reminder prompt for next try
                format_reminder_prompt = report_format_reminder_prompt
                prompt = prompt + format_reminder_prompt

                # if max try time reached, raise error
                if try_time == self.config["max_try_time"]:
                    raise ValueError("Failed to generate response after max try time")
            else:
                response_with_thought = f"<think>{thought}</think>\n{action}"
                context_length = len(prompt) + len(response_with_thought)
                self.context_cnt.append(context_length)

                return thought, action

    def postprocess_response(self, response):
        """Make sure the response is in the correct format.
        Args:
            response: response text
        Returns:
            processed response, if the format is not correct, return None
        """

        # Count occurrences of each tag
        tag_counts = {}
        for action in ACTIONS:
            start_tag = f"<{action}>"
            end_tag = f"</{action}>"
            start_count = response.count(start_tag)
            end_count = response.count(end_tag)
            tag_counts[action] = {"start": start_count, "end": end_count}

        # Validate tag format rules
        if tag_counts["summary"]["start"] == 0:
            valid_actions = []
            for action in ACTIONS:
                start_count = tag_counts[action]["start"]
                end_count = tag_counts[action]["end"]

                # Tags must appear in pairs and at most once
                if start_count != end_count or start_count > 1:
                    return None

                # If this action's tags appeared once, record as valid action
                if start_count == 1:
                    valid_actions.append(action)

            # Only one action is allowed per response
            if len(valid_actions) != 1:
                return None

            # Extract content between valid action tags
            action = valid_actions[0]
            pattern = f"<{action}>(.*?)</{action}>"
            match = re.search(pattern, response, re.DOTALL)
            if match:
                content = match.group(1).strip()
                return f"<{action}>{content}</{action}>"
        else:
            # Find the first occurrence of <summary>
            start_idx = response.find("<summary>")
            # Find the last occurrence of </summary>
            end_idx = response.rfind("</summary>")

            if start_idx == -1 or end_idx == -1:
                return None  # No <summary> or </summary> tag found

            # Extract content between the first <summary> and last </summary>
            content = response[start_idx + len("<summary>") : end_idx].strip()
            return f"<summary>{content}</summary>"

        return None

    def execute_response(self, response, num_docs, do_search=True):
        """
        Args:
            response: response
            num_docs: number of documents to retrieve
            do_search: whether to perform search
        Returns:
            done: whether the task is done
            observation: list of return information of this turn
        """
        action, content = self.parse_action(response)
        next_obs = ""
        done = False
        updated_history = False
        search_query = content if action == "search" else ""

        if do_search and search_query != "":
            search_results, urls = self.search(search_query, num_docs)
        else:
            urls = []

        if action == "answer":
            done = True
        elif action == "search":
            self.search_cnt += 1
            self.consecutive_search_cnt += 1
            # observation = f'**Search Queries**  {1}.{search_query}  **Fetched URLS**  {1}.{urls[0].strip()}'
            if len(urls) == 0:
                urls.append("Did not return any URL")
            observation = f"""**Search Queries**

1. {search_query}

**Fetched URLS**

1. {urls[0].strip()}"""
            next_obs = observation
        elif action == "plan":
            self.consecutive_search_cnt = 0
        elif action == "scripts":
            self.consecutive_search_cnt = 0
            self.script_cnt += 1
        elif action == "summary":
            next_obs = "You performed a summary action in this turn. The content of this action is ignored since your history turns information has been updated according to it.\n"
            self.consecutive_search_cnt = 0
            self.summary_cnt += 1
            self.summary_history = content
            updated_history = True
        else:
            raise ValueError(f"Invalid action: {action}")

        return done, updated_history, next_obs

    def parse_action(self, action):
        """Parse the action to get the action type and content.
        Args:
            action: action, format ensured by postprocess_response
        Returns:
            action_type: action type
            content: action content
        """
        # Find the first occurrence of '<' and '>' to extract action_type
        start_tag_open = action.find("<")
        start_tag_close = action.find(">", start_tag_open)
        if start_tag_open == -1 or start_tag_close == -1:
            raise ValueError(f"Invalid action format: {action}")

        action_type = action[start_tag_open + 1 : start_tag_close]

        # Find the last occurrence of '</' and '>' to locate the closing tag
        end_tag_open = action.rfind("</")
        end_tag_close = action.rfind(">", end_tag_open)
        if end_tag_open == -1 or end_tag_close == -1:
            raise ValueError(f"Invalid action format: {action}")

        # Extract content between the first '>' and last '</'
        content = action[start_tag_close + 1 : end_tag_open].strip()

        return action_type, content

    def _update_input(
        self, input, cur_response, next_obs, updated_history, original_prompt
    ):
        """Update the input with the history.
        Args:
            input: input
            cur_response: current response
            next_obs: next observation
            updated_history: whether update the history to agent summary
            original_prompt: original prompt for the question
        Returns:
            updated input
        """

        if updated_history:
            context = (
                f"[Turn 1 - Turn {self.num_env_steps - 1}]:\n{self.summary_history}\n\n"
            )
            context += f"[Turn {self.num_env_steps}]:\n{next_obs}\n\n"
            new_input = original_prompt + context
        else:
            context = f"[Turn {self.num_env_steps}]:\n{cur_response}\n{next_obs}\n\n"
            new_input = input + context

        # add reminder for search and final report
        if self.consecutive_search_cnt > self.config["search_reminder_turn"]:
            new_input += f"\n\nNote: You have performed {self.consecutive_search_cnt} search actions. Please consider update your report scripts or output the final report. If you still want to search, make sure you check history search results and DO NOT perform duplicate search."
        if self.num_env_steps > self.config["final_report_reminder_turn"]:
            new_input += f"\n\nNote: You have performed {self.num_env_steps} turns. Please consider output the final report. If you still want to search, make sure you check history search results and DO NOT perform duplicate search."

        input_length = len(new_input)
        if input_length > MAX_CONTEXT_LENGTH:
            new_input = new_input + summary_reminder_prompt

        return new_input

    def _compose_final_output(self, response):
        if "</answer>" in response:
            return response.split("<answer>")[1].split("</answer>")[0]
        else:
            return "did not find answer"

    def search(self, query, num_docs):
        print(f"Searching for: {query}")
        documents, urls = query_clueweb(query, num_docs=num_docs)
        info_retrieved = "\n\n".join(documents)
        print(f"Search completed. Found {len(documents)} documents")
        return info_retrieved, urls

    def remove_markdown_blocks(self, text):
        text = re.sub(r"^```", "", text, flags=re.MULTILINE)
        text = re.sub(r"``$", "", text, flags=re.MULTILINE)
        return text


@app.route("/health", methods=["GET"])
def health_check():
    """
    Basic health check endpoint
    """
    return jsonify(
        {
            "status": "healthy",
            "service": "Simple DeepResearch Server",
            "port": 5003,
            "endpoints": {
                "/health": "Health check",
                "/test-connections": "Test all API connections",
                "/test-openai": "Test OpenAI API connection",
                "/test-perplexity": "Test Perplexity API connection",
                "/run": "Main research endpoint",
            },
        }
    )


@app.route("/test-connections", methods=["GET"])
def test_api_connections():
    """
    Test endpoint to verify Gemini, Serper, OpenAI, and Perplexity API connections
    """
    results = {
        "gemini": {"status": "unknown", "message": ""},
        "serper": {"status": "unknown", "message": ""},
        "openai": {"status": "unknown", "message": ""},
        "perplexity": {"status": "unknown", "message": ""},
        "overall_status": "unknown",
    }

    # Test Gemini API
    try:
        if not GEMINI_API_KEY:
            results["gemini"]["status"] = "error"
            results["gemini"]["message"] = "GEMINI_API_KEY not set"
        else:
            # Test Gemini with a simple request
            client = genai.Client(api_key=GEMINI_API_KEY)
            test_response = client.models.generate_content(
                model=MODEL_ID_Flash, contents="Say 'Hello' if you can read this."
            )

            if test_response and test_response.candidates:
                results["gemini"]["status"] = "success"
                results["gemini"]["message"] = "Connected successfully"
            else:
                results["gemini"]["status"] = "error"
                results["gemini"]["message"] = "No response from Gemini API"

    except Exception as e:
        results["gemini"]["status"] = "error"
        results["gemini"]["message"] = f"Error: {str(e)}"

    # Test Serper API
    try:
        if not SERPER_API_KEY:
            results["serper"]["status"] = "error"
            results["serper"]["message"] = "SERPER_API_KEY not set"
        else:
            # Test Serper with a simple search
            documents, urls = query_serper("test search", num_docs=1)

            if documents and len(documents) > 0:
                results["serper"]["status"] = "success"
                results["serper"][
                    "message"
                ] = f"Connected successfully, found {len(documents)} results"
            else:
                results["serper"]["status"] = "warning"
                results["serper"]["message"] = "Connected but no results returned"

    except Exception as e:
        results["serper"]["status"] = "error"
        results["serper"]["message"] = f"Error: {str(e)}"

    # Test OpenAI API
    try:
        if not OPENAI_API_KEY:
            results["openai"]["status"] = "error"
            results["openai"]["message"] = "OPENAI_API_KEY not set"
        else:
            # Test OpenAI with a simple completion
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
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

    # Test Perplexity API
    try:
        if not PERPLEXITY_API_KEY:
            results["perplexity"]["status"] = "error"
            results["perplexity"]["message"] = "PERPLEXITY_API_KEY not set"
        else:
            # Test Perplexity with a simple request
            headers = {
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {"role": "user", "content": "Say 'Hello' if you can read this."}
                ],
                "max_tokens": 10,
            }

            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=payload,
                timeout=10,
            )

            if response.status_code == 200:
                results["perplexity"]["status"] = "success"
                results["perplexity"]["message"] = "Connected successfully"
            else:
                results["perplexity"]["status"] = "error"
                results["perplexity"][
                    "message"
                ] = f"HTTP {response.status_code}: {response.text[:100]}"

    except Exception as e:
        results["perplexity"]["status"] = "error"
        results["perplexity"]["message"] = f"Error: {str(e)}"

    # Determine overall status
    success_count = sum(
        1
        for service in ["gemini", "serper", "openai", "perplexity"]
        if results[service]["status"] in ["success", "warning"]
    )

    if success_count >= 3:
        results["overall_status"] = "success"
    elif success_count >= 2:
        results["overall_status"] = "partial"
    elif success_count >= 1:
        results["overall_status"] = "limited"
    else:
        results["overall_status"] = "error"

    return jsonify(results)


@app.route("/test-openai", methods=["GET"])
def test_openai_connection():
    """
    Test endpoint specifically for OpenAI API connection
    """
    result = {"service": "openai", "status": "unknown", "message": ""}

    try:
        if not OPENAI_API_KEY:
            result["status"] = "error"
            result["message"] = "OPENAI_API_KEY not set"
        else:
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Test connection"}],
                max_tokens=5,
            )

            if response and response.choices:
                result["status"] = "success"
                result["message"] = "OpenAI API connected successfully"
                result["model_used"] = "gpt-3.5-turbo"
            else:
                result["status"] = "error"
                result["message"] = "No response from OpenAI API"

    except Exception as e:
        result["status"] = "error"
        result["message"] = f"Error: {str(e)}"

    return jsonify(result)


@app.route("/test-perplexity", methods=["GET"])
def test_perplexity_connection():
    """
    Test endpoint specifically for Perplexity API connection
    """
    result = {"service": "perplexity", "status": "unknown", "message": ""}

    try:
        if not PERPLEXITY_API_KEY:
            result["status"] = "error"
            result["message"] = "PERPLEXITY_API_KEY not set"
        else:
            headers = {
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [{"role": "user", "content": "Test connection"}],
                "max_tokens": 5,
            }

            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=payload,
                timeout=10,
            )

            if response.status_code == 200:
                result["status"] = "success"
                result["message"] = "Perplexity API connected successfully"
                result["model_used"] = "llama-3.1-sonar-small-128k-online"
            else:
                result["status"] = "error"
                result["message"] = (
                    f"HTTP {response.status_code}: {response.text[:100]}"
                )

    except Exception as e:
        result["status"] = "error"
        result["message"] = f"Error: {str(e)}"

    return jsonify(result)


@app.route("/run", methods=["POST"])
def return_model_response():

    # Support both 'input' and 'question' parameter names for compatibility
    question = request.json.get("question") or request.json.get("input")

    prompt = report_prompt.format(question=question)

    config = {
        "max_turns": 30,  # max number of turns
        "num_docs": 1,  # number of documents to retrieve
        "max_try_time": 5,  # max number of tries to generate a response
        # number of turns to remind the agent to stop search and revise the report
        # scripts or output the final report (only for long report)
        "search_reminder_turn": 5,
        # number of turns to remind the agent to output the final report (only for
        # long report)
        "final_report_reminder_turn": 15,
    }

    agent = LLMAgent(config, is_flash=False)

    print(f"Model: {agent.model_name}")

    def generate():
        for step_data in agent.run_llm_loop(prompt):
            yield f"data: {json.dumps(step_data)}\n\n"

    response = Response(
        generate(),
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",  # Add if needed for CORS
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )

    return response


if __name__ == "__main__":
    print("\n=== Starting Simple DeepResearch Server ===")
    print("Available endpoints:")
    print("  GET  /health - Health check")
    print("  GET  /test-connections - Test all API connections")
    print("  GET  /test-openai - Test OpenAI API connection")
    print("  GET  /test-perplexity - Test Perplexity API connection")
    print("  POST /run - Main research endpoint")
    print("===============================================\n")
    app.run(debug=False, port=5003)
