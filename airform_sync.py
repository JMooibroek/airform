from playwright.sync_api import sync_playwright

class WebPageInteraction:
    def __init__(self):
        self.id_count = 0
        self.clickable_ids = {}
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.page = self.browser.new_page()

    # Function to check if an element is visible
    def is_visible(self, element):
        return element.evaluate("el => el.offsetWidth > 0 && el.offsetHeight > 0 && window.getComputedStyle(el).visibility !== 'hidden'")

    # Function to truncate long strings
    def truncate_string(self, s, max_length=30):
        return s if len(s) <= max_length else f"...{s[-max_length:]}"

    def navigate(self, url):
        """Navigate to url, returns True on success"""
        try:
            self.page.goto(url)
            return True
        except Exception as e:
            print("Something went wrong: ",e)
            return False

    def close(self):
        self.browser.close()

    def get_markdown(self, max_lines=0):
        page_title = self.page.title()
        elements = self.page.query_selector_all("body *")
        markdown_lines = [f"title={page_title}"]
        self.id_count = 0
        self.clickable_ids = {}

        for element in elements:
            visible = self.is_visible(element)
            if visible:
                tag_name = element.evaluate("el => el.tagName.toLowerCase()")

                # If tag is interactable element
                if tag_name in ["input", "a", "select", "button", "img"]:
                    self.clickable_ids[self.id_count] = element
                    id_suffix = f"${self.id_count}"
                    if tag_name == 'img':
                        src = element.evaluate("el => el.src")
                        alt = element.evaluate("el => el.alt") or "Image"
                        truncated_src = self.truncate_string(src)
                        markdown_lines.append(f"![{alt}]({truncated_src}){id_suffix}")                    
                    elif tag_name == 'input':
                        input_type = element.evaluate("el => el.type")
                        input_placeholder = element.evaluate("el => el.placeholder") or ""
                        label = element.evaluate("el => el.previousElementSibling ? el.previousElementSibling.innerText : ''")
                        markdown_lines.append(f"?{input_type}[{input_placeholder}]({label}){id_suffix}")
                    elif tag_name == 'textarea':
                        input_placeholder = element.inner_text()
                        label = element.evaluate("el => el.previousElementSibling ? el.previousElementSibling.innerText : ''")
                        markdown_lines.append(f"?textarea[{input_placeholder}]({label}){id_suffix}")
                    elif tag_name == 'a':
                        href = element.evaluate("el => el.href")
                        text = element.inner_text()
                        markdown_lines.append(f"[{text}]({href}){id_suffix}")
                    elif tag_name == 'button':
                        text = element.inner_text()
                        markdown_lines.append(f"?button[{text}]{id_suffix}")
                    elif tag_name == 'select':
                        options = element.query_selector_all("option")
                        option_texts = [option.inner_text() for option in options]
                        label = element.evaluate("el => el.previousElementSibling ? el.previousElementSibling.innerText : ''")
                        markdown_lines.append(f'?select["{", ".join(option_texts)}"]({label}){id_suffix}')
                    self.id_count += 1
                else:
                    click = element.evaluate("el => el.ondblclick !== null || el.onclick !== null")
                    if click:
                        self.clickable_ids[self.id_count] = element
                        id_suffix = f"${self.id_count}"
                        self.id_count += 1
                    else:
                        id_suffix = ""

                    if tag_name == 'h1':
                        text = element.inner_text()
                        markdown_lines.append(f"# {text}{id_suffix}")
                    elif tag_name == 'h2':
                        text = element.inner_text()
                        markdown_lines.append(f"## {text}{id_suffix}")
                    elif tag_name == 'h3':
                        text = element.inner_text()
                        markdown_lines.append(f"### {text}{id_suffix}")
                    elif tag_name == 'h4':
                        text = element.inner_text()
                        markdown_lines.append(f"#### {text}{id_suffix}")
                    elif tag_name == 'h5':
                        text = element.inner_text()
                        markdown_lines.append(f"##### {text}{id_suffix}")
                    elif tag_name == 'h6':
                        text = element.inner_text()
                        markdown_lines.append(f"###### {text}{id_suffix}")
                    elif tag_name == 'p':
                        text = element.inner_text()
                        markdown_lines.append(f"{text}{id_suffix}")
                    elif tag_name == 'strong':
                        text = element.inner_text()
                        markdown_lines.append(f"**{text}**{id_suffix}")
                    elif tag_name == 'em':
                        text = element.inner_text()
                        markdown_lines.append(f"*{text}*{id_suffix}")
                    elif tag_name == 'b':
                        text = element.inner_text()
                        markdown_lines.append(f"**{text}**{id_suffix}")
                    elif tag_name == 'i':
                        text = element.inner_text()
                        markdown_lines.append(f"*{text}*{id_suffix}")
                    elif tag_name == 'mark':
                        text = element.inner_text()
                        markdown_lines.append(f"`{text}`{id_suffix}")
                    elif tag_name == 'blockquote':
                        text = element.inner_text()
                        markdown_lines.append(f"> {text}{id_suffix}")
                    elif tag_name == 'pre':
                        text = element.inner_text()
                        markdown_lines.append(f"```\n{text}\n```{id_suffix}")
                    elif tag_name == 'table':
                        rows = element.query_selector_all("tr")
                        table_markdown = []
                        for row in rows:
                            cells = row.query_selector_all("td, th")
                            cell_texts = [cell.inner_text() for cell in cells]
                            table_markdown.append("| " + " | ".join(cell_texts) + " |")
                        markdown_lines.append("\n".join(table_markdown))
                    elif tag_name == 'ul':
                        items = element.query_selector_all("li")
                        for item in items:
                            text = item.inner_text()
                            markdown_lines.append(f"- {text}{id_suffix}")
                    elif tag_name == 'ol':
                        items = element.query_selector_all("li")
                        for index, item in enumerate(items, start=1):
                            text = item.inner_text()
                            markdown_lines.append(f"{index}. {text}{id_suffix}")
                    else:
                        parent_text = element.evaluate("el => Array.from(el.childNodes).filter(node => node.nodeType === Node.TEXT_NODE).map(node => node.textContent.trim()).join(' ')")
                        parent_text = parent_text.strip()
                        markdown_lines.append(parent_text)
                        
                    if markdown_lines[-1] == '' or markdown_lines[-1].isspace():
                        del markdown_lines[-1]
                    elif len(markdown_lines) >= max_lines and max_lines != 0:
                        return "\n".join(markdown_lines)

        # id_count is 1 bigger than actual size
        return "\n".join(markdown_lines)

    def click(self, id, double: bool):
        """Clicks on element, returns True on success"""
        element = self.clickable_ids[id]
        if element:
            if double:
                element.dblclick()
            else:
                element.click()
            return True
        else:
            return False

    def fill_in(self, id, input_value, enter: bool):
        """Fills input element, returns True on success"""
        element = self.clickable_ids[id]
        if element:
            element.fill(input_value)
            if enter:
                element.press("Enter")
            return True
        else:
            return False

    def select(self, id, option_text):
        """Selects element, returns True on success"""
        element = self.clickable_ids[id]
        if element:
            element.select_option(option_text)
            return True
        else:
            return False

# For testing purposes
def main(url):
    interaction = WebPageInteraction()
    interaction.navigate(url)
    markdown_output = interaction.get_markdown()
    print(markdown_output)
    interaction.close()

if __name__ == "__main__":
    main("https://jamaro.net/")