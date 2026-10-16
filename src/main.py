import os
import json
import logging
import groq
from groq import Groq
from dotenv import load_dotenv

from tools import add_numbers, multiply_numbers
from tool_schema import tool_to_schema

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. Initialize the Groq client
client = Groq(
    api_key=os.environ["GROQ_API_KEY"],
    max_retries=2,
    timeout=30.0
    )

MODEL = "openai/gpt-oss-120b"


def request_completion(messages, tools):
    try:
        return client.chat.completions.create(
            model= MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

    except groq.RateLimitError:
        logger.warning("Groq API rate limit reached.")
        print("Groq rate limit reached. Please wait and try again.")

    except groq.AuthenticationError:
        logger.error("Authentication failed. Check your API key.")
        print("Authentication failed. Please check your API key.")

    except groq.APIConnectionError:
        logger.error("Failed to connect to the Groq API.")
        print("Connection error. Please check your network and try again.")

    except groq.APIStatusError as error:
        logger.error("Groq API returned an error status. %s", error.status_code)
        print(f"Groq API error (HTTP {error.status_code}).")

    except groq.APIError:
        logger.exception("Unexpected Groq SDK error.")
        print("An unexpected API error occurred.")

    except Exception:
        logger.exception("Unexpected error during Groq request.")
        print("An unexpected error occurred.")

    return None



# 2. Create python tools



# 3. define the tool schema / Tell the LLM which tools are available
tools = [
    tool_to_schema(add_numbers),
    tool_to_schema(multiply_numbers)
]


# 4. Connect tools names with python functions
available_tools = {
    "add_numbers": add_numbers,
    "multiply_numbers": multiply_numbers
}


def execute_tool(tool_call, available_tools):
    tool_name = tool_call.function.name

    # check whether the tool is available
    if tool_name not in available_tools:
        return {
            "success": False,
            "error": f"Unknown tool : {tool_name}"
        }
    
    # Parse the tool arguments from the tool call
    try:
        arguments = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": f"Tool arguments are not valid JSON: {arguments}"
        }

    # Ensure arguments are a JSON dictionary
    if not isinstance(arguments, dict):
        return {
            "success": False,
            "error": f"Tool arguemnts must be a JSON dictionary: {arguments}"
        }
    

    # Executing tool.
    try:
        result = available_tools[tool_name](**arguments)

        return {
            "success": True,
            "result": result
        }
    
    except (TypeError, ValueError) as error:
        logger.warning(
            "invalid arguments for tool %s: %s", 
            tool_name, 
            error
        )

        return {
            "success": False,
            "error": "Invalid tool arguments. Check the parameters name and values."
        }
    
    except Exception:
        logger.exception(
            "Unexpected failure in executing tool %s: ", tool_name)

        return {
            "success": False,
            "error": "The tool failed unexpectedly."
        }



# 5. Build the agent and its feedback loop
def run_agent(user_input):
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful math agent. "
                "Use the provided tools for calculations. "
                "After receiving tool results, answer the user. "
                "If needed, you may call another tool."
            )
        },
        {
            "role": "user",
            "content": user_input
        }
    ]

    iteration = 0
    max_iteration = 5

    while iteration < max_iteration:
        iteration += 1
        print(f"\n--- Loop iteration {iteration} ---")

        # Call the Groq API to get the model's response
        response = request_completion(messages, tools)

        if response is None:
            print("Agent stopped because the API request failed.")
            return None
        
        if not response.choices:
            print("Agent stopped: the model returned no choices.")
            return None

        assistant_message = response.choices[0].message
        
        if assistant_message is None:
            print("Agent stopped: the model returned an empty message.")
            return None

        # append into messages
        messages.append(assistant_message)

        if not assistant_message.tool_calls:
            final_answer = assistant_message.content

            if not final_answer:
                print("Agent stopped: the model returned no answer.")
                return None

            print(f"Assistant: {final_answer}")
            print("Agent ended")
            return final_answer
        
        # If tool avl, then call each tool
        for tool_call in assistant_message.tool_calls:

            if (
                tool_call is None
                or not getattr(tool_call, "id", None)
                or not getattr(tool_call, "function", None)
                or not getattr(tool_call.function, "name", None)
            ):
                print("Skipping malformed tool call.")
                continue
            
            tool_result = execute_tool(tool_call, available_tools)

            print(f"Tool result: {tool_result}")

            # send the tool result back to the llm to get the final answer
            messages.append({
                "role": "tool",
                "name": tool_call.function.name,
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result)
            })

        print("Agent stopped!")


# Run the agent
question = input("Ask a math question (e.g., 'What is 5 + 3?'): ")
run_agent(question)