import os
import json
from groq import Groq
from dotenv import load_dotenv

from tools import add_numbers, multiply_numbers
from tool_schema import tool_to_schema

# Load environment variables from .env file
load_dotenv()

# 1. Initialize the Groq client
client = Groq(api_key=os.environ["GROQ_API_KEY"])

MODEL = "openai/gpt-oss-120b"

# 2. Create python tools



# 3. define the tool schema / Tell the LLM which tools are available
tools = [
    tool_to_schema(add_numbers),
    tool_to_schema(multiply_numbers)
]



from pprint import pprint

pprint(tools, sort_dicts=False)


# 4. Connect tools names with python functions
available_tools = {
    "add_numbers": add_numbers,
    "multiply_numbers": multiply_numbers
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
        response = client.chat.completions.create(
            model= MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        assistant_message = response.choices[0].message
        print(f"Assistant: {assistant_message.content}")

        # append into messages
        messages.append(assistant_message)

        if not assistant_message.tool_calls:
            print("Agent ended")
            return assistant_message.content
        
        # If tool avl, then call each tool
        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(
                tool_call.function.arguments
            )

            print("Tool name: ", tool_name)
            print("Arguments: ", arguments)

            # calling the python function / passing the arguments into the python function to get the result
            tool_result = available_tools[tool_name](**arguments)

            print(f"Tool result: {tool_result}")

            # send the tool result back to the llm to get the final answer
            messages.append({
                "role": "tool",
                "name": tool_name,
                "tool_call_id": tool_call.id,
                "content": json.dumps({"result": tool_result})
            })

        print("Agent stopped!")


# Run the agent
question = input("Ask a math question (e.g., 'What is 5 + 3?'): ")
run_agent(question)