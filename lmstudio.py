import signal
import sys
import json
from openai import OpenAI
from airform import WebPageInteraction  # Import the WebPageInteraction class
import asyncio

# Point to the local server
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
model = "lmstudio-community/qwen2.5-7b-instruct"



async def main():
    # Initialize a WebPageInteraction instance
    interaction = await WebPageInteraction().open()

    # Define the tool functions
    async def navigate_tool(url: str):
        await interaction.navigate(url)
        output = await interaction.get_markdown(100)
        return output

    async def get_webpage():
        output = await interaction.get_markdown(100)
        return output

    async def click_tool(id: int, double: bool):
        result = await interaction.click(id, bool)
        if result:
            return f"Clicked on element with ID {id}"
        else:
            return "Something went wrong"

    async def fill_in_tool(id: int, input_value: str):
        result = await interaction.fill_in(id, input_value)
        if result:
            return f"Filled in element with ID {id_suffix} with value '{input_value}'"
        else:
            return "Something went wrong"

    async def select_tool(id: int, option_text: str):
        result = await interaction.select(id, option_text)
        if result:
            return f"Selected option '{option_text}' from element with ID {id_suffix}"
        else:
            return "Something went wrong"

    # Tools definition
    tools = [
        {
            "type": "function",
            "function": {
                "name": "navigate_tool",
                "description": "Navigate to a specified URL. Returns the webpage in markdown format",
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
                "name": "get_webpage",
                "description": "Returns the current webpage content in markdown format.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
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
                        "double": {
                            "type": "bool",
                            "description": "Whether to double click.",
                        },
                    },
                    "required": ["id", "double"],
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
                    },
                    "required": ["id", "input_value"],
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

    messages = [
        {
            "role": "system",
            "content": """You are a helpful assistant with web browsing capabilities. 
            Use the supplied tools to assist the user. Use DuckDuckGo (https://duckduckgo.com/?q=query+here) as search engine.
            If the user asks a question you can't answer, keep using tools untill you can answer the user.
            The markdown format includes interactable html elements. These elements end with $0, where 0 is the id""",
        }
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

        # LM Studio
        response = client.chat.completions.create(  # No await here
            model=model,
            messages=messages,
            tools=tools,
        )


        # Check for tool calls
        tool_calls = response.choices[0].message.tool_calls if response.choices[0].message.tool_calls else []

        if tool_calls:
            print("\nModel response requesting tool call:\n", flush=True)
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                # Call the appropriate tool function based on the tool name
                if tool_name == "navigate_tool":
                    result = await navigate_tool(arguments["url"])
                elif tool_name == "get_webpage":
                    result = await get_webpage()
                elif tool_name == "click_tool":
                    result = await click_tool(arguments["id"], arguments["double"])
                elif tool_name == "fill_in_tool":
                    result = await fill_in_tool(arguments["id"], arguments["input_value"])
                elif tool_name == "select_tool":
                    result = await select_tool(arguments["id"], arguments["option_text"])

                # Create a message containing the result of the function call
                function_call_result_message = {
                    "role": "tool",
                    "content": json.dumps({"result": result}),
                    "tool_call_id": tool_call.id,
                }

                # Insert markdown output into messages
                # markdown_output = f"**Tool Result:** {result}"  # Example markdown output
                # markdown_output = await interaction.get_markdown()
                messages.append({
                    "role": "tool",
                    "content": result,
                })

                print("Tool result:\n" + result)

                # Prepare the chat completion call payload
                completion_messages_payload = [
                    *messages,  # Append the updated messages
                    {
                        "role": "assistant",
                        "tool_calls": [tool_call],
                    },
                    function_call_result_message,
                ]

                # Call the OpenAI API's chat completions endpoint to send the tool call result back to the model
                response = client.chat.completions.create(  # No await here
                    model=model,
                    messages=completion_messages_payload,
                )
        
        # If no tool calls, just get the assistant's message
        assistant_message = response.choices[0].message.content
        print(f"\nAI: {assistant_message}")
        # Add AI message to messages
        messages.append({
            "role": "assistant",
            "content": assistant_message,
        })

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass