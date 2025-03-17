from playwright.sync_api import sync_playwright
from html.parser import HTMLParser
from bs4 import BeautifulSoup
import re
import math
import time

print_execution_duration = True

class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.markdown = ""
        self.page = None

        # List variables
        self.is_list_ordered = []
        self.list_order_count = []

        # Element variables
        self.visible = True
        self.depth = 0
        self.href = None
        self.element_count = {}
        self.check_visibility = True
        self.strip_newlines = False

        # ID's
        self.id_count = 0
        self.clickable_ids = []

    def truncate_string_middle(self, s, max_length=20):
        return s if len(s) <= max_length else f"{s[0:max_length]}...{s[-max_length:]}"
    
    def handle_starttag(self, tag, attrs):
        if tag not in self.element_count:
            self.element_count[tag] = 0
        else:
            self.element_count[tag] += 1
        if self.visible:
            if tag in ['script', 'noscript', 'head', 'meta', 'style', 'link', 'title', 'template']:
                self.visible = False
                self.depth = 1
                return
            else:
                
                locator = self.page.locator(tag).nth(self.element_count[tag])
            
                if self.check_visibility and locator.is_hidden():
                    self.visible = False
                    self.depth = 1
                    return
                
                if tag not in ['a', 'button', 'img', 'input', 'textarea', 'svg'] and locator.evaluate(f"el => el.ondblclick !== null || el.onclick !== null"):
                    self.clickable_ids.append(locator)
                    self.markdown += f"\n{self.id_count}="
                    self.id_count += 1

                attrs_dict = dict(attrs)

                # if tag == 'div':
                #     self.markdown += "\n"
                if tag == 'h1':
                    self.markdown += "\n# "
                elif tag == 'h2':
                    self.markdown += "\n## "
                elif tag == 'h3':
                    self.markdown += "\n### "
                elif tag == 'h4':
                    self.markdown += "\n#### "
                elif tag == 'h5':
                    self.markdown += "\n##### "
                elif tag == 'h6':
                    self.markdown += "\n###### "
                elif tag == 'p':
                    self.markdown += "\n"
                elif tag == 'ul':
                    self.is_list_ordered.append(False)
                elif tag == 'ol':
                    self.list_order_count.append(1)
                    self.is_list_ordered.append(True)
                elif tag == 'li':
                    self.markdown += "    " * (len(self.is_list_ordered) - 1)
                    if self.is_list_ordered[-1]:
                        self.markdown += f"\n{self.list_order_count[-1]}. "
                        self.list_order_count[-1] += 1
                    else:
                        self.markdown += "\n- "
                elif tag == 'strong' or tag == 'b':
                    self.markdown += " **"
                elif tag == 'em' or tag == 'i':
                    self.markdown += " *"
                elif tag == 'blockquote':
                    self.markdown += "> "
                elif tag == 'code':
                    self.markdown += "`"
                elif tag == 'pre':
                    self.markdown += "\n```\n"
                elif tag == 'img':
                    alt_text = attrs_dict.get('alt', 'image').strip("\n")
                    src = attrs_dict.get('src', '')
                    self.markdown += f"![{self.id_count}={alt_text}]({self.truncate_string_middle(src)}) "
                    self.clickable_ids.append(locator)
                    self.id_count += 1
                elif tag == 'a':
                    self.strip_newlines = True
                    self.href = attrs_dict.get('href', '')
                    self.markdown += f"[{self.id_count}="
                    self.clickable_ids.append(locator)
                    self.id_count += 1
                elif tag == 'button':
                    self.strip_newlines = True
                    self.markdown += f"<button id={self.id_count}>"
                    self.clickable_ids.append(locator)
                    self.id_count += 1
                elif tag == 'input':
                    self.strip_newlines = True
                    type = attrs_dict.get('type', 'text')
                    properties = ''
                    value = attrs_dict.get('value', '')
                    if value:
                        properties += f" value={value}"
                    # if type in ['number', 'range', 'datetime-local', 'datetime', 'date', 'time', 'week', 'month']:
                    min = attrs_dict.get('min', '')
                    max = attrs_dict.get('max', '')
                    if min:
                        properties += f" min={min}"
                    if max:
                        properties += f" max={max}"
                    if type == 'checkbox' or type == 'radio':
                        if 'checked' in attrs_dict:
                            properties += ' checked'
                        else:
                            properties += ' unchecked'
                    if type == 'file':
                        properties += ' ' + attrs_dict.get(' multiple', ' single')
                    self.markdown += f"<input id={self.id_count} type={type}{properties}>"
                    self.clickable_ids.append(locator)
                    self.id_count += 1
                elif tag == 'select':
                    self.markdown += "<select>"
                elif tag == 'select':
                    self.markdown += "<option>"
                elif tag == 'textarea':
                    self.strip_newlines = True
                    self.markdown += f"<textarea id={self.id_count}>"
                    self.clickable_ids.append(locator)
                    self.id_count += 1
                elif tag == 'br':
                    self.markdown += "\n"
                elif tag == 'svg':
                    self.markdown += f"![{self.id_count}=SVG]()"
                    self.clickable_ids.append(locator)
                    self.id_count += 1
                    self.visible = False
                    self.depth = 1
                elif tag == 'fieldset' or tag == 'address':
                    self.markdown += "\n---\n"
        else:
            self.depth += 1

    def handle_endtag(self, tag):
        if tag == 'br':
            self.markdown += "\n"
        if self.visible:
            if tag in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'blockquote']:
                self.markdown += "\n"
            elif tag in ['button', 'textarea', 'select', 'option']:
                self.markdown += f"</{tag}>"
            elif tag == 'ul':
                self.is_list_ordered.pop()
            elif tag == 'ol':
                self.list_order_count.pop()
                self.is_list_ordered.pop()
            elif tag == 'strong' or tag == 'b':
                self.markdown += "** "
            elif tag == 'em' or tag == 'i':
                self.markdown += "* "
            elif tag == 'code':
                self.markdown += "`"
            elif tag == 'pre':
                self.markdown += "\n```\n"
            elif tag == 'a':
                try:
                    self.markdown += f"]({self.href.strip()})"
                except:
                    self.markdown += "](error)"
            elif tag == 'fieldset' or tag == 'address':
                self.markdown += "\n---\n"
        else:
            self.depth -= 1
            if self.depth <= 0:
                self.visible = True

    def handle_data(self, data):
        if self.visible:
            if self.strip_newlines:
                self.markdown += data.strip().strip("\n")
                self.strip_newlines = False
            else:
                self.markdown += data.strip()

    def get_markdown(self, page, check_visibility=True):
        self.__init__()
        self.page = page
        self.check_visibility = check_visibility
        html = self.page.inner_html('body')
        soup = BeautifulSoup(html, features="html.parser")
        html = soup.prettify(formatter="minimal")
        self.feed(html)
        self.id_count -= 1
        return re.sub(r'\n{3,}', '\n', self.markdown)

class WebPageInteraction:
    # def __init__(self):
    #     self.id_count = 0
    #     self.clickable_ids = {}
        
    # Open page
    @classmethod
    def open(self):
        self = WebPageInteraction()
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36')
        self.page = self.context.new_page()
        self.parser = MyHTMLParser()
        self.url = self.page.url
        self.title = self.page.title()
        self.markdown = ""
        return self

    def set_url(self, url):
        """Navigate to url, returns [True/False, message] on success"""
        try:
             self.page.goto(url, wait_until="domcontentloaded")
        except:
            return False, "Error: could not navigate to page. Are you sure this page exists?"
        self.convert_page()
        return True, f"Navigated to {url}"

    def close(self):
         self.context.close()

    def get_page_part(self, max_lines, part):
        """Returns partial content of page. Part 1 is the top part"""
        if print_execution_duration:
            start_time = time.time()
        self.page.wait_for_load_state('domcontentloaded')  # Time-out to prevent loading text before site is fully loaded
        if print_execution_duration:
            print("\n--- %s seconds ---\n" % (time.time() - start_time))
        part -= 1
        markdown_lines = self.markdown.splitlines(keepends=True)
        result = ''.join(markdown_lines[(max_lines * part):((max_lines * (part)) + max_lines)])
        total_parts = math.ceil(len(markdown_lines) / max_lines)
        return f"title: {self.title}\nurl: {self.url}\n```markdown\n" + result + f"\n```\nShowing part {part+1} of {total_parts}"

    def convert_page(self):
        """Load the current webpage in markdown"""
        self.url = self.page.url
        self.title = self.page.title()
        self.markdown = self.parser.get_markdown(self.page, True)
        return True

    def click(self, id, double_click: bool):
        """Clicks on element, returns [True/False, message] on success"""
        if id > self.parser.id_count:
            return False, "Error: id outside range"
        element = self.parser.clickable_ids[id]
        if element:
            if double_click:
                try:
                     element.dblclick()
                except:
                    return False, "Error: could not click on element. Are you sure this is a button/link?"
                return True, f"Double clicked on ${id}"
            else:
                try:
                     element.click()
                except:
                    return False, "Error: could not double click on element. Are you sure this is a button/link?"
                return True, f"Clicked on ${id}"
        else:
            return False, "Error: element does not exist"

    def fill_in(self, id, input_value, enter: bool):
        """Fills input element, returns [True/False, message] on success"""
        try:
            id = int(id)
        except:
            return False, "Error: id is not an integer"
        if id > self.parser.id_count:
            return False, "Error: id outside range"
        element = self.parser.clickable_ids[id]
        if element:
            try:
                 element.fill(input_value)
            except:
                return False, "Error: could not fill element. Are you sure this is an input?"
            if enter:
                 element.press("Enter")
            return True, f"Filled in ${id}, with value {input_value}."
        else:
            return False, "Error: element does not exist"

    def select(self, id, option_text):
        """Selects element, returns [True/False, message] on success"""
        if id > self.parser.id_count:
            return False, "Error: id outside range"
        element = self.parser.clickable_ids[id]
        if element:
            try:
                 element.select_option(option_text)
            except:
                return False, "Error: could select element. Are you sure this is a select and the value is correct?"
            return True, f"Selected {option_text} from ${id}"
        else:
            return False, "Error: element does not exist"
        
    def wait(self):
        self.page.wait_for_timeout(5000)
        return True, "Waited for 5 seconds"

# For testing purposes
def main(url):
    interaction = WebPageInteraction().open()
    code, response = interaction.set_url(url)
    print(response)
    interaction.convert_page()
    print(interaction.get_page_part(50,1))
    interaction.close()

if __name__ == "__main__":
    main("https://jamaro.net/")