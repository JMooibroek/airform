import signal
import sys
import json
from openai import OpenAI
from airform_async import WebPageInteraction 
import asyncio

# True prints tool results, False only prints LLM response
verbose = True

# Point to the local server
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
model = "lmstudio-community/qwen2.5-7b-instruct"


async def main():
    # Context for LLM
    messages = [{
            "role": "system",
            "content": """You are an AI assistant with web browsing capabilities.
Use the supplied tools to assist the user. Preferably use DuckDuckGo (https://duckduckgo.com/?q=query+here) as search engine.
You can use multiple tool calls in one go (for example filling in multiple input fields). After tool call(s) the webpage is returned in markdown format.
The markdown format includes interactable html elements. These elements end with $0, where 0 is the id.
Difficult tasks require more tool calls. Keep using tool calls until you can conclude the task/question.""",}]

    # Initialize a WebPageInteraction instance
    interaction = await WebPageInteraction().open()

    async def process_tools(tool_calls):
        if verbose:
            print("\nModel response requesting tool call(s):\n", flush=True)

        tool_call_results = []

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            all_good = True

            code = None
            response = None

            # Call the appropriate tool function based on the tool name
            if tool_name == "navigate_tool":
                code, response = await interaction.navigate(arguments["url"])
                if verbose:
                    print("url: " + arguments["url"])
                if code == False:
                    all_good = False
            elif tool_name == "click_tool":
                code, response = await interaction.click(arguments["id"], arguments["double_click"])
            elif tool_name == "fill_in_tool":
                code, response = await interaction.fill_in(arguments["id"], arguments["input_value"], arguments["enter"])
            elif tool_name == "select_tool":
                code, response = await interaction.select(arguments["id"], arguments["option_text"])

            if verbose:
                print("Error: " + str(code) + "\n" + response)

            messages.append({
                    "role": "tool",
                    "content": "Error: " + str(code) + "\n" + response,
                })
            
        return all_good

    # Tools definition
    tools = [
        {
            "type": "function",
            "function": {
                "name": "navigate_tool",
                "description": "Navigate to a specified URL.",
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
                "name": "click_tool",
                "description": "Click on an interactive element identified by its ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "int",
                            "description": "The ID of the element to click.",
                        },
                        "double_click": {
                            "type": "bool",
                            "description": "Whether to double click.",
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
                "name": "fill_in_tool",
                "description": "Fill in an input field identified by its ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "int",
                            "description": "The ID of the input field to fill.",
                        },
                        "input_value": {
                            "type": "string",
                            "description": "The value to input.",
                        },
                        "enter": {
                            "type": "bool",
                            "description": "Whether to press return after fill.",
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
                "name": "select_tool",
                "description": "Select an option from a dropdown identified by its ID.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "int",
                            "description": "The ID of the select element.",
                        },
                        "option_text": {
                            "type": "int",
                            "description": "The text of the option to select.",
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
                result = await process_tools(tool_calls)
                
                if result:
                    # add webpage to message history
                    webpage = await interaction.get_markdown()
                    messages.append({
                        "role": "tool",
                        "content": webpage,
                    })
                    if verbose:
                        print("Webpage:\n" + webpage)
                    
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