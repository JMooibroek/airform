import signal
import sys
import json
from openai import OpenAI
from airform_async import WebPageInteraction 
import asyncio

# True prints tool results, False only prints LLM response
verbose = True

# Determines how many lines at once are given the the LLM
max_lines = 100

# Point to the local server
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
model = "lmstudio-community/qwen2.5-7b-instruct"


async def main():
    # Context for LLM
    messages = [{
            "role": "system",
            "content": """You are an AI assistant with web browsing capabilities. The web browse tools give you access to the internet.
Preferably use DuckDuckGo (https://duckduckgo.com/?q=query+here) as search engine.
Some tools can be used in succession (for example filling in multiple input fields), other tools are single call only. After tool call(s) the webpage is returned in markdown format.
The markdown format includes interactable html elements. These elements end with $0, where 0 is the id.
Difficult tasks require more tool calls. Keep using tool calls until you can conclude the task/question.""",}]

    # Initialize a WebPageInteraction instance
    print("Opening web browser...")
    interaction = await WebPageInteraction().open()

    async def process_tools(tool_calls):
        if verbose:
            print("\nModel response requesting tool call(s):\n", flush=True)

        for tool_call in tool_calls:
            # WARNING: Don't use capitals in function names
            tool_name = tool_call.function.name.lower()
            arguments = json.loads(tool_call.function.arguments)
            single_call = False

            # Call the appropriate tool function based on the tool name
            if tool_name == "goto":
                code, response = await interaction.goto(arguments["url"], max_lines)
                single_call = True
            elif tool_name == "scrollto":
                code, response = await interaction.get_page(arguments["line"], arguments["line"] + max_lines)
                single_call = True
            elif tool_name == "click":
                code, response = await interaction.click(arguments["id"], arguments["double_click"])
            elif tool_name == "fill":
                code, response = await interaction.fill_in(arguments["id"], arguments["input_value"], arguments["enter"])
            elif tool_name == "select":
                code, response = await interaction.select(arguments["id"], arguments["option_text"])
            else:
                code = False
                response = "Tool '"+tool_name+"' does not exist"

            if verbose:
                if code == False:
                    print("Error: " + response)
                else:
                    print("Tool response: " + response)

            messages.append({
                "role": "assistant",
                "tool_calls": [{
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": tool_call.function,
                    }]})
            messages.append({
                    "role": "tool",
                    "content": response,
                    "tool_call_id": tool_call.id,
                })
            
            if single_call:
                if code:
                    return True
                else:
                    return False
            
        code, response = await interaction.get_page(0, max_lines)
        messages.append({
                    "role": "tool",
                    "content": response,
                    "tool_call_id": tool_call.id,
                })
        if verbose:
            if code == False:
                print("Error: " + response)
            else:
                print("Tool response: " + response)
        return True

    # Tools definition
    tools = [
        {
            "type": "function",
            "function": {
                "name": "goto",
                "description": "Opens a webpage of a specified URL. Single call",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL to navigate to.",
                        },
                    },
                    "required": ["url"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "scrollto",
                "description": "scroll to a specified line. Single call",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "line": {
                            "type": "int",
                            "description": "The line to scroll to",
                        },
                    },
                    "required": ["line"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "click",
                "description": "Click on an element identified by its ID. Elements can be links, buttons and other elements",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "int",
                            "description": "The ID of the element to click",
                        },
                        "double_click": {
                            "type": "bool",
                            "description": "True: double click. False: single click",
                        },
                    },
                    "required": ["id", "double_click"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "fill",
                "description": "Fill a value in an input field or textarea identified by its ID",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "int",
                            "description": "The ID of the input field to fill",
                        },
                        "input_value": {
                            "type": "string",
                            "description": "The value to input",
                        },
                        "enter": {
                            "type": "bool",
                            "description": "True: press return after fill",
                        },
                    },
                    "required": ["id", "input_value", "enter"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "select",
                "description": "Select an option from a dropdown identified by its ID",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "int",
                            "description": "The ID of the select element",
                        },
                        "option_text": {
                            "type": "int",
                            "description": "The text of the option to select",
                        },
                    },
                    "required": ["id", "option_text"],
                    "additionalProperties": False,
                },
            },
        },
    ]

    print("Type 'exit' to quit")

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == "exit" or user_input.lower() == "quit":
            print("closing...")
            await interaction.close()
            break
        
        # Add user message to the conversation
        messages.append({
            "role": "user",
            "content": user_input,
        })

        while True:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tools,
                )
            except Exception as e:
                print("An error has occured. Are you sure the LM Studio server is running?: ", e)
            # Check for tool calls
            tool_calls = response.choices[0].message.tool_calls if response.choices[0].message.tool_calls else []
            if tool_calls:
                code = await process_tools(tool_calls)
                                    
            else:
                assistant_message = response.choices[0].message.content
                print(f"\nAI: {assistant_message}")
                # Add AI message to messages
                messages.append({
                    "role": "assistant",
                    "content": assistant_message,
                })
                break

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass