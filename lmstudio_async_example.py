import signal
import sys
import json
import lmstudio as lms
from airform_async import WebPageInteraction  # Import the WebPageInteraction class
import asyncio

# Global var
interaction = None

# Define the tool functions
def navigate_tool(url: str):
    """Navigate to a specified URL. Returns the webpage"""
    print(f"Tool: navigate to {url}\n")
    global interaction
    loop = asyncio.get_event_loop()
    nav = asyncio.run_coroutine_threadsafe(interaction.navigate(url), loop).result()
    print(nav)
    if nav:
        output = asyncio.run_coroutine_threadsafe(interaction.get_markdown(30), loop).result()
        print(output)
        return output
    else:
        return "Failed"

def click_tool(id: int, double: bool):
    """Click on an element. Returns the updated webpage"""
    print("Tool: click\n")
    global interaction
    loop = asyncio.get_event_loop()
    if asyncio.run_coroutine_threadsafe(interaction.click(id, double), loop).result():
        return asyncio.run_coroutine_threadsafe(interaction.get_markdown(), loop).result()
    else:
        return "Failed"

def fill_in_tool(id: int, input_value: str, enter: bool):
    """Fill in an input/textarea by its id. Returns the updated webpage"""
    print("Tool: fill\n")
    global interaction
    loop = asyncio.get_event_loop()
    if asyncio.run_coroutine_threadsafe(interaction.fill_in(id, input_value, enter), loop).result():
        return asyncio.run_coroutine_threadsafe(interaction.get_markdown(), loop).result()
    else:
        return "Failed"

def select_tool(id: int, option_text: str):
    """Select an option by its text of a dropdown by its id. Returns the updated webpage"""
    print("Tool: select\n")
    global interaction
    loop = asyncio.get_event_loop()
    if asyncio.run_coroutine_threadsafe(interaction.select(id, option_text), loop).result():
        return asyncio.run_coroutine_threadsafe(interaction.get_markdown(), loop).result()
    else:
        return "Failed"

def print_fragment(fragment, round_index=0):
    # .act() supplies the round index as the second parameter
    print(fragment.content, end="", flush=True)

async def main():
    # Initialize a WebPageInteraction instance
    print("Starting web browser...")
    global interaction
    interaction = await WebPageInteraction().open()

    try:
        model = lms.llm()
    except:
        print("No model loaded")
        return

    chat = lms.Chat("""You are a helpful assistant with web browsing capabilities. Webpages are displayed in markdown format.
    The markdown format includes interactable html elements. These elements end with $0, where 0 is the id.
    Use the supplied tools to assist the user. Use DuckDuckGo as search engine.""")

    print("Type 'exit' to quit")

    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() == "exit" or user_input.lower() == "quit":
                print("closing...")
                await interaction.close()  # Close asynchronously
                break
        except EOFError:
            print()
            break
        if not user_input:
            break
        chat.add_user_message(user_input)
        print("AI: ", end="", flush=True)
        await model.act(
            chat,
            [navigate_tool, click_tool, fill_in_tool, select_tool],
            on_message=chat.append,
            on_prediction_fragment=print_fragment,
        )
        
        print()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass