import signal
import sys
import json
import lmstudio as lms
from airform_sync import WebPageInteraction

# Global var
interaction = None

# Define the tool functions
def navigate_tool(url: str):
    """Navigate to a specified URL. Returns the webpage"""
    print(f"Tool: navigate to {url}\n")
    global interaction
    nav = interaction.navigate(url)
    print(nav)
    if nav:
        output = interaction.get_markdown(30)
        print(output)
        return output
    else:
        return "Failed"

def click_tool(id: int, double: bool):
    """Click on an element. Returns the updated webpage"""
    print("Tool: click\n")
    global interaction
    if interaction.click(id, double):
        return interaction.get_markdown()
    else:
        return "Failed"

def fill_in_tool(id: int, input_value: str, enter: bool):
    """Fill in an input/textarea by its id. Returns the updated webpage"""
    print("Tool: fill\n")
    global interaction
    if interaction.fill_in(id, input_value, enter):
        return interaction.get_markdown()
    else:
        return "Failed"

def select_tool(id: int, option_text: str):
    """Select an option by its text of a dropdown by its id. Returns the updated webpage"""
    print("Tool: select\n")
    global interaction
    if interaction.select(id, option_text):
        return interaction.get_markdown()
    else:
        return "Failed"

def print_fragment(fragment, round_index=0):
    # .act() supplies the round index as the second parameter
    print(fragment.content, end="", flush=True)


def main():
    # Initialize a WebPageInteraction instance
    print("Starting web browser...")
    global interaction
    interaction = WebPageInteraction()

    try:
        model = lms.llm()
    except:
        print("No model loaded")
        return

    chat = lms.Chat("""You are a helpful assistant with web browsing capabilities. Webpages are displayed in markdown format.
    The markdown format includes interactable html elements. These elements end with $0, where 0 is the id.
    Use the supplied tools to assist the user. Use DuckDuckGo (https://duckduckgo.com/?q=query+here) as search engine.""")

    print("Type 'exit' to quit")

    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() == "exit" or user_input.lower() == "quit":
                print("closing...")
                interaction.close() 
                break
        except EOFError:
            print()
            break
        if not user_input:
            break
        chat.add_user_message(user_input)
        print("AI: ", end="", flush=True)
        model.act(
            chat,
            [navigate_tool, click_tool, fill_in_tool, select_tool],
            on_message=chat.append,
            on_prediction_fragment=print_fragment,
        )
        
        print()

def func():
    interaction = WebPageInteraction()
    interaction.navigate("https://jamaro.net")
    markdown_output = interaction.get_markdown()
    print(markdown_output)
    interaction.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass