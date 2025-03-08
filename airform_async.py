import asyncio
from playwright.async_api import async_playwright
import re

class WebPageInteraction:
    def __init__(self):
        self.id_count = 0
        self.clickable_ids = {}
        
    # Open page
    @classmethod
    async def open(self):
        self = WebPageInteraction()
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.page = await self.browser.new_page()
        return self
    
    # Function to check if an element is visible
    async def is_visible(self, element):
        return await element.evaluate("el => el.offsetWidth > 0 && el.offsetHeight > 0 && window.getComputedStyle(el).visibility !== 'hidden'")

    # Function to truncate long strings
    def truncate_string(self, s, max_length=30):
        return s if len(s) <= max_length else f"...{s[-max_length:]}"

    async def goto(self, url, max_lines):
        """Navigate to url, returns True on success"""
        try:
            await self.page.goto(url, wait_until="load")
        except:
            return False, "Error: could not navigate to page. Are you sure this page exists?"
        try:
            await self.get_markdown()
        except:
            return False, "Error: could not convert to markdown"
        if max_lines == 0:
            max_lines = len(self.page_lines)
        elif max_lines > len(self.page_lines):
            max_lines = len(self.page_lines)

        code, page = await self.get_page(0, max_lines)
        return code, page

    async def close(self):
        await self.browser.close()

    async def get_page(self, from_line, to_line):
        if to_line == 0:
            to_line = len(self.page_lines)
        elif to_line > len(self.page_lines):
            to_line = len(self.page_lines)
        page_title = await self.page.title()
        try:
            markdown = "\n".join(self.page_lines[from_line:to_line])
        except:
            return False, "Error: could not retrieve page"
        page = f"url: {self.page.url}\ntitle: {page_title}\n{markdown}\n---\nShowing lines {from_line} to {to_line} of " + str(len(self.page_lines))
        return True, page

    async def get_markdown(self):
        if self.page.url == "about:blank":
            return "title=about:blank"
        
        elements = await self.page.query_selector_all("body *")
        self.page_lines = []
        self.id_count = 0
        self.clickable_ids = {}

        for element in elements:
            visible = await self.is_visible(element)
            if visible:
                tag_name = await element.evaluate("el => el.tagName.toLowerCase()")

                line = ""

                # If tag is interactable element
                if tag_name in ["input", "a", "select", "button", "img"]:
                    self.clickable_ids[self.id_count] = element
                    id_suffix = f"${self.id_count}"
                    if tag_name == 'img':
                        click = await element.evaluate("el => el.ondblclick !== null || el.onclick !== null")
                        clickable = ""
                        if click:
                            clickable = ":clickable"
                        src = await element.evaluate("el => el.src")
                        alt = await element.evaluate("el => el.alt") or "Image"
                        truncated_src = self.truncate_string(src)
                        line = f"![{alt}]({truncated_src}){clickable}{id_suffix}"
                    elif tag_name == 'input':
                        input_type = await element.evaluate("el => el.type")
                        input_placeholder = await element.evaluate("el => el.placeholder") or ""
                        label = await element.evaluate("el => el.previousElementSibling ? el.previousElementSibling.innerText : ''")
                        line = f"?input:{input_type}[{input_placeholder}]({label}){id_suffix}"
                    elif tag_name == 'textarea':
                        input_placeholder = await element.inner_text()
                        label = await element.evaluate("el => el.previousElementSibling ? el.previousElementSibling.innerText : ''")
                        line = f"?textarea[{input_placeholder}]({label}){id_suffix}"
                    elif tag_name == 'a':
                        href = await element.evaluate("el => el.href")
                        text = await element.inner_text()
                        line = f"[{text}]({href}){id_suffix}"
                    elif tag_name == 'button':
                        text = await element.inner_text()
                        line = f"?button[{text}]{id_suffix}"
                    elif tag_name == 'select':
                        options = await element.query_selector_all("option")
                        option_texts = [await option.inner_text() for option in options]
                        label = await element.evaluate("el => el.previousElementSibling ? el.previousElementSibling.innerText : ''")
                        line = f'?select["{", ".join(option_texts)}"]({label}){id_suffix}'
                    self.id_count += 1
                else:
                    click = await element.evaluate("el => el.ondblclick !== null || el.onclick !== null")
                    if click:
                        self.clickable_ids[self.id_count] = element
                        id_suffix = f":clickable${self.id_count}"
                        self.id_count += 1
                    else:
                        id_suffix = ""

                    if tag_name == 'h1':
                        text = await element.inner_text()
                        line = f"# {text}{id_suffix}"
                    elif tag_name == 'h2':
                        text = await element.inner_text()
                        line = f"## {text}{id_suffix}"
                    elif tag_name == 'h3':
                        text = await element.inner_text()
                        line = f"### {text}{id_suffix}"
                    elif tag_name == 'h4':
                        text = await element.inner_text()
                        line = f"#### {text}{id_suffix}"
                    elif tag_name == 'h5':
                        text = await element.inner_text()
                        line = f"##### {text}{id_suffix}"
                    elif tag_name == 'h6':
                        text = await element.inner_text()
                        line = f"###### {text}{id_suffix}"
                    elif tag_name == 'p':
                        text = await element.inner_text()
                        line = f"{text}{id_suffix}"
                    elif tag_name == 'strong':
                        text = await element.inner_text()
                        line = f"**{text}**{id_suffix}"
                    elif tag_name == 'em':
                        text = await element.inner_text()
                        line = f"*{text}*{id_suffix}"
                    elif tag_name == 'b':
                        text = await element.inner_text()
                        line = f"**{text}**{id_suffix}"
                    elif tag_name == 'i':
                        text = await element.inner_text()
                        line = f"*{text}*{id_suffix}"
                    elif tag_name == 'mark':
                        text = await element.inner_text()
                        line = f"`{text}`{id_suffix}"
                    elif tag_name == 'blockquote':
                        text = await element.inner_text()
                        line = f"> {text}{id_suffix}"
                    elif tag_name == 'pre':
                        text = await element.inner_text()
                        line = f"```\n{text}\n```{id_suffix}"
                    elif tag_name == 'table':
                        rows = await element.query_selector_all("tr")
                        table_markdown = []
                        for row in rows:
                            cells = await row.query_selector_all("td, th")
                            cell_texts = [await cell.inner_text() for cell in cells]
                            table_markdown.append("| " + " | ".join(cell_texts) + " |")
                        line = "\n".join(table_markdown)
                    elif tag_name == 'ul':
                        items = await element.query_selector_all("li")
                        for item in items:
                            text = await item.inner_text()
                            line = f"- {text}{id_suffix}"
                    elif tag_name == 'ol':
                        items = await element.query_selector_all("li")
                        for index, item in enumerate(items, start=1):
                            text = await item.inner_text()
                            line = f"{index}. {text}{id_suffix}"
                    elif tag_name not in ['script', 'meta', 'link', 'area']:
                        parent_text = await element.evaluate("el => Array.from(el.childNodes).filter(node => node.nodeType === Node.TEXT_NODE).map(node => node.textContent.trim()).join(' ')")
                        parent_text = parent_text.strip()
                        line = parent_text
                        
                # Python, why are you like this?
                if not (not line or line.isspace()):
                    self.page_lines.append(line)
                    
        
        self.id_count -= 1
        return True

    async def click(self, id, double_click: bool):
        """Clicks on element, returns True on success"""
        if id > self.id_count:
            return False, "Error: id outside range"
        element = self.clickable_ids[id]
        if element:
            if double_click:
                try:
                    await element.dblclick()
                except:
                    return False, "Error: could not click on element. Are you sure this is a button/link?"
                return True, f"Clicked on ${id}"
            else:
                try:
                    await element.click()
                except:
                    return False, "Error: could not double click on element. Are you sure this is a button/link?"
                return True, f"Double clicked on ${id}"
        else:
            return False, "Error: element does not exist"

    async def fill_in(self, id, input_value, enter: bool):
        """Fills input element, returns True on success"""
        if id > self.id_count:
            return False, "Error: id outside range"
        element = self.clickable_ids[id]
        if element:
            try:
                await element.fill(input_value)
            except:
                return False, "Error: could not fill element. Are you sure this is an input?"
            if enter:
                await element.press("Enter")
            return True, f"Filled in ${id}, with value {input_value}."
        else:
            return False, "Error: element does not exist"

    async def select(self, id, option_text):
        """Selects element, returns True on success"""
        if id > self.id_count:
            return False, "Error: id outside range"
        element = self.clickable_ids[id]
        if element:
            try:
                await element.select_option(option_text)
            except:
                return False, "Error: could select element. Are you sure this is a select and the value is correct?"
            return True, f"Selected {option_text} from ${id}"
        else:
            return False, "Error: element does not exist"

# For testing purposes
async def main(url):
    interaction = await WebPageInteraction().open()
    code, response = await interaction.goto(url, 0)
    print(response)
    await interaction.close()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main("https://jamaro.net/"))
    except KeyboardInterrupt:
        pass