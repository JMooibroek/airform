import json
from openai import OpenAI
from airform_sync import WebPageInteraction 
import urllib.parse

# Print markdown in command-line
print_markdown = True

# Determines how many lines at once are given the the LLM
max_lines = 50

# Point to the local server
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
model = "lmstudio-community/qwen2.5-7b-instruct"



SYSTEM_PROMPT = """You are an AI robot browsing the web, just like humans. After tool call(s) the webpage is returned in markdown format with numerical ID's.
You can:
1. Click on an element
2. Enter text in an textbox
3. Select an option
4. Scroll to a page part. The part 1 is shown by default. You may need to scroll down (>2) to find more information if more parts are available.
5. Wait for 5 seconds. Used if the page hasn't fully loaded yet.
6. Enter a URL.
7. Search. This uses DuckDuckGo. It can be used for, among other things: calculations, retrieve (real-time) data like news, find images, get weather
Guidelines you MUST follow:
1. Use keywords when searching
2. Don't fill in buttons, or other elements that can't be filled in.
3. Avoid repeating the same action. Continuous use of wait is not allowed
4. Only answer when you have completed the task
5. Don't login or sign-in unless specifically asked by the user.
6. You aren't able to view images, videos, or listen to audio
7. Information must come from a source.
8. Continue your task until it is complete or the information is gathered
"""


def main():
    # Context for LLM
    messages = [{
            "role": "system",
            "content": SYSTEM_PROMPT,}]

    # Initialize a WebPageInteraction instance
    print("Opening web browser...")
    interaction = WebPageInteraction().open()

    def process_tools(tool_calls):
        def add_tool_message(tool_call, response):
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
        
        for tool_call in tool_calls:
            # WARNING: Don't use capitals in function names, they will get filtered
            tool_name = tool_call.function.name.lower()
            print("Using " + tool_name + " tool\n")
            arguments = json.loads(tool_call.function.arguments)
            response = ""

            # Call the appropriate tool function based on the tool name
            if tool_name in ['goto', 'search', 'scrollto']:
                if len(arguments) == 0:
                    code = False
                    response = "No arguments given"
                page_part = 1
                if tool_name == "goto":
                    code, response = interaction.set_url(arguments["url"])
                elif tool_name == "search":
                    code, response = interaction.set_url("https://duckduckgo.com/?q=" + urllib.parse.quote_plus(arguments["query"]))
                elif tool_name == "scrollto":
                    page_part = arguments["part"]
                    code = True

                print("Tool response: " + response + "\n")
                if code:
                    markdown = interaction.get_page_part(max_lines, page_part)
                    add_tool_message(tool_call, markdown)
                    if print_markdown:
                        print(markdown)
                else:
                    add_tool_message(tool_call, response)
                return True
            else:
                if tool_name == "click":
                    code, response = interaction.click(arguments["id"], arguments["double_click"])
                elif tool_name == "fill":
                    code, response = interaction.fill_in(arguments["id"], arguments["input_value"], arguments["enter"])
                elif tool_name == "select":
                    code, response = interaction.select(arguments["id"], arguments["option_text"])
                elif tool_name == "wait":
                    code, response = interaction.wait()
                else:
                    response = "Tool '"+tool_name+"' does not exist"

                add_tool_message(tool_call, response)
                print("Tool response: " + response + "\n")
                
        interaction.convert_page()
        markdown = interaction.get_page_part(max_lines, 1)
        messages.append({
                    "role": "tool",
                    "content": markdown
                })
        if print_markdown:
            print(markdown)
        return True

    # Tools definition
    tools = [
        {
            "type": "function",
            "function": {
                "name": "goto",
                "description": "Opens a webpage of a specified URL",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL to navigate to",
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
                "name": "search",
                "description": "Searches on DuckDuckGo for a query",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The query to search for",
                        },
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "scrollto",
                "description": "scroll to a specific page part",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "part": {
                            "type": "int",
                            "description": "The numerical part to scroll to",
                        },
                    },
                    "required": ["part"],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "wait",
                "description": "wait for 5 seconds",
                "parameters": {
                    "type": "object",
                    "properties": {
                    },
                    "required": [],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "click",
                "description": "Click on a button, link, or other element identified by its ID",
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
                "description": "Fill a value in an input field or textarea identified by its ID. Works only on `<input>`",
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
                "description": "Select an option from a dropdown identified by its ID. Works only on `<select>`",
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
            interaction.close()
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
                process_tools(tool_calls)
                                    
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
    main()