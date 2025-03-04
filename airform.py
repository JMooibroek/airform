import asyncio
from playwright.async_api import async_playwright

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

    async def navigate(self, url):
        await self.page.goto(url)

    async def close(self):
        await self.browser.close()

    async def get_markdown(self, max_lines):
        page_title = await self.page.title()
        elements = await self.page.query_selector_all("body *")
        markdown_lines = [f"title={page_title}"]
        self.id_count = 0
        self.clickable_ids = {}

        for element in elements:
            visible = await self.is_visible(element)
            if visible:
                tag_name = await element.evaluate("el => el.tagName.toLowerCase()")

                # If tag is interactable element
                if tag_name in ["input", "a", "select", "button", "img"]:
                    self.clickable_ids[self.id_count] = element
                    id_suffix = f"${self.id_count}"
                    if tag_name == 'img':
                        src = await element.evaluate("el => el.src")
                        alt = await element.evaluate("el => el.alt") or "Image"
                        truncated_src = self.truncate_string(src)
                        markdown_lines.append(f"![{alt}]({truncated_src}){id_suffix}")
                    elif tag_name == 'input':
                        input_type = await element.evaluate("el => el.type")
                        input_placeholder = await element.evaluate("el => el.placeholder") or ""
                        label = await element.evaluate("el => el.previousElementSibling ? el.previousElementSibling.innerText : ''")
                        markdown_lines.append(f"?{input_type}[{input_placeholder}]({label}){id_suffix}")
                    elif tag_name == 'a':
                        href = await element.evaluate("el => el.href")
                        text = await element.inner_text()
                        markdown_lines.append(f"[{text}]({href}){id_suffix}")
                    elif tag_name == 'button':
                        text = await element.inner_text()
                        markdown_lines.append(f"?button[{text}]{id_suffix}")
                    elif tag_name == 'select':
                        options = await element.query_selector_all("option")
                        option_texts = [await option.inner_text() for option in options]
                        label = await element.evaluate("el => el.previousElementSibling ? el.previousElementSibling.innerText : ''")
                        markdown_lines.append(f'?select["{", ".join(option_texts)}"]({label}){id_suffix}')
                    self.id_count += 1
                else:
                    click = await element.evaluate("el => el.ondblclick !== null || el.onclick !== null")
                    if click:
                        self.clickable_ids[self.id_count] = element
                        id_suffix = f"${self.id_count}"
                        self.id_count += 1
                    else:
                        id_suffix = ""

                    if tag_name == 'h1':
                        text = await element.inner_text()
                        markdown_lines.append(f"# {text}{id_suffix}")
                    elif tag_name == 'h2':
                        text = await element.inner_text()
                        markdown_lines.append(f"## {text}{id_suffix}")
                    elif tag_name == 'h3':
                        text = await element.inner_text()
                        markdown_lines.append(f"### {text}{id_suffix}")
                    elif tag_name == 'h4':
                        text = await element.inner_text()
                        markdown_lines.append(f"#### {text}{id_suffix}")
                    elif tag_name == 'h5':
                        text = await element.inner_text()
                        markdown_lines.append(f"##### {text}{id_suffix}")
                    elif tag_name == 'h6':
                        text = await element.inner_text()
                        markdown_lines.append(f"###### {text}{id_suffix}")
                    elif tag_name == 'p':
                        text = await element.inner_text()
                        markdown_lines.append(f"{text}{id_suffix}")
                    elif tag_name == 'strong':
                        text = await element.inner_text()
                        markdown_lines.append(f"**{text}**{id_suffix}")
                    elif tag_name == 'em':
                        text = await element.inner_text()
                        markdown_lines.append(f"*{text}*{id_suffix}")
                    elif tag_name == 'b':
                        text = await element.inner_text()
                        markdown_lines.append(f"**{text}**{id_suffix}")
                    elif tag_name == 'i':
                        text = await element.inner_text()
                        markdown_lines.append(f"*{text}*{id_suffix}")
                    elif tag_name == 'mark':
                        text = await element.inner_text()
                        markdown_lines.append(f"`{text}`{id_suffix}")
                    elif tag_name == 'blockquote':
                        text = await element.inner_text()
                        markdown_lines.append(f"> {text}{id_suffix}")
                    elif tag_name == 'pre':
                        text = await element.inner_text()
                        markdown_lines.append(f"```\n{text}\n```{id_suffix}")
                    elif tag_name == 'table':
                        rows = await element.query_selector_all("tr")
                        table_markdown = []
                        for row in rows:
                            cells = await row.query_selector_all("td, th")
                            cell_texts = [await cell.inner_text() for cell in cells]
                            table_markdown.append("| " + " | ".join(cell_texts) + " |")
                        markdown_lines.append("\n".join(table_markdown))
                    elif tag_name == 'ul':
                        items = await element.query_selector_all("li")
                        for item in items:
                            text = await item.inner_text()
                            markdown_lines.append(f"- {text}{id_suffix}")
                    elif tag_name == 'ol':
                        items = await element.query_selector_all("li")
                        for index, item in enumerate(items, start=1):
                            text = await item.inner_text()
                            markdown_lines.append(f"{index}. {text}{id_suffix}")
                    else:
                        parent_text = await element.evaluate("el => Array.from(el.childNodes).filter(node => node.nodeType === Node.TEXT_NODE).map(node => node.textContent.trim()).join(' ')")
                        parent_text = parent_text.strip()
                        markdown_lines.append(parent_text)
                        
                    if markdown_lines[-1] == '' or markdown_lines[-1].isspace():
                        del markdown_lines[-1]
                    elif len(markdown_lines) >= max_lines:
                        return "\n".join(markdown_lines)
                    
        
        # id_count is 1 bigger than actual size
        return "\n".join(markdown_lines)

    async def click(self, id, double: bool):
        element = self.clickable_ids[id]
        if element:
            if double:
                await element.dblclick()
            else:
                await element.click()
        else:
            return False

    async def fill_in(self, id, input_value):
        element = self.clickable_ids[id]
        if element:
            await element.fill(input_value)
        else:
            return False

    async def select(self, id, option_text):
        element = self.clickable_ids[id]
        if element:
            await element.select_option(option_text)
            return
        else:
            return False

# For testing purposes
async def main(url):
    interaction = await WebPageInteraction().open()
    await interaction.navigate(url)
    markdown_output = await interaction.get_markdown()
    print(markdown_output)
    await interaction.close()

if __name__ == "__main__":
    asyncio.run(main("https://duckduckgo.com/?q=Jamaro+Mooibroek+age"))