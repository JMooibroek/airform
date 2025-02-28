from playwright.sync_api import sync_playwright

def truncate_end(string, width):
    if len(string) > width:
        string = string[:width-3] + '...'
    return string


def convert_to_airform(url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url)
        
        
        # Counter for interactive elements
        id_counter = 0

        # Function to recursively parse elements
        def parse_element(element, indent_level=0):
            nonlocal id_counter
            
            # if element.is_hidden():
            #     return ""
                
            
            tag_name = element.evaluate('el => el.tagName.toLowerCase()')
            content = ""

            # Handle headings
            if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(tag_name[1])
                return '#' * level + ' ' + element.inner_text() + '\n'

            # Handle text formatting
            if tag_name in ['strong', 'b']:
                content = f"**{element.inner_text()}**"
            elif tag_name in ['em', 'i']:
                content = f"*{element.inner_text()}*"
            elif tag_name == 'mark':
                content = f"=={element.inner_text()}=="
            elif tag_name == 'blockquote':
                content = '> ' + element.inner_text()
            elif tag_name == 'pre':
                content = "```\n" + element.inner_text() + "\n```"
            elif tag_name == 'p':
                content = element.inner_text() + "\n"

            # Handle lists
            if tag_name in ['ul', 'ol']:
                list_items = element.query_selector_all('li')
                for item in list_items:
                    bullet = '- ' if tag_name == 'ul' else '1. '
                    content += '  ' * indent_level + bullet + parse_element(item, indent_level + 1).strip() + '\n'

            # Handle links and images
            if tag_name == 'a':
                href = element.get_attribute('href')
                content = f"[{element.inner_text()}]({href})\n"
            elif tag_name == 'img':
                src = element.get_attribute('src')
                alt = element.get_attribute('alt') or ''
                content = f"![{alt}]({truncate_end(src,30)})\n"

            # Handle tables
            if tag_name == 'table':
                rows = element.query_selector_all('tr')
                for row in rows:
                    cells = row.query_selector_all('td, th')
                    content += '|' + '|'.join([cell.inner_text() for cell in cells]) + '|\n'

            # Handle forms
            if tag_name in ['input', 'textarea', 'button', 'select']:
                placeholder = element.get_attribute('placeholder') or ''
                type_attr = element.get_attribute('type') or 'text'
                label = element.get_attribute('label') or ''
                if tag_name == 'input':
                    content = f"input[{placeholder}]({type_attr}){{{label}}}${id_counter}\n"
                    id_counter += 1
                elif tag_name == 'textarea':
                    content = f"input[{placeholder}](textarea){{{label}}}${id_counter}\n"
                    id_counter += 1
                elif tag_name == 'button':
                    content = f"button[{element.inner_text()}]{{{label}}}${id_counter}\n"
                    id_counter += 1
                elif tag_name == 'select':
                    options = element.query_selector_all('option')
                    option_texts = [opt.inner_text() for opt in options]
                    content = f'select[{", ".join(option_texts)}]{{{label}}}${id_counter}\n'
                    id_counter += 1

            # Handle semantic tags
            if tag_name in ['header', 'footer', 'nav', 'article', 'section', 'aside', 'main']:
                content = tag_name + '\n'

            # Loop through all child elements
            children = element.query_selector_all(':scope > *')
            for child in children:
                child_content = parse_element(child, indent_level + 1)
                if child_content:
                    content += '  ' * indent_level + child_content

            return content

        # Start parsing from the body
        body = page.query_selector('body')
        airform_content = "title=" + truncate_end(page.title(), 30) + "\n"
        airform_content += parse_element(body)
        browser.close()
        return airform_content

# Example usage
output = convert_to_airform("https://jamaro.net")
print(output)