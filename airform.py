# airform.py

import urllib.request
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup

class Airform:
    def __init__(self):
        pass

    def fetch_html(self, url):
        """Fetch HTML content from a given URL using urllib."""
        try:
            with urllib.request.urlopen(url) as response:
                return response.read().decode('utf-8')
        except HTTPError as e:
            print(f"HTTP error: {e.code} - {e.reason}")
            return None
        except URLError as e:
            print(f"URL error: {e.reason}")
            return None

    def convert_to_airform(self, html_content):
        """Convert HTML content into AI Readable FORMat (airform)."""
        soup = BeautifulSoup(html_content, 'html.parser')
        airform_output = []

        # Function to recursively extract and format elements
        def extract_elements(element):
            if element.name is None:  # If the element is a NavigableString
                text = element.strip()
                if text:
                    airform_output.append(f"txt: {text}")

            elif element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                airform_output.append(f"{element.name}: {element.get_text()}")

            elif element.name == 'p':
                airform_output.append(f"p: {element.get_text()}")

            elif element.name == 'ul':
                airform_output.append("ul:")
                for li in element.find_all('li'):
                    airform_output.append(f"  - {li.get_text()}")

            elif element.name == 'ol':
                airform_output.append("ol:")
                for li in element.find_all('li'):
                    airform_output.append(f"  - {li.get_text()}")

            elif element.name == 'blockquote':
                airform_output.append(f"blockquote: {element.get_text()}")

            elif element.name == 'img':
                alt_text = element.get('alt', 'No alt text provided')
                src = element.get('src', 'No source provided')
                airform_output.append(f"img: {src} alt: {alt_text}")

            # Recursively process children if the element has any
            if hasattr(element, 'children'):
                for child in element.children:
                    extract_elements(child)

        # Start extraction from the body of the HTML
        for child in soup.body.children:
            extract_elements(child)

        return "\n".join(airform_output)

    def process_url(self, url):
        """Fetch and convert HTML content from a URL."""
        html_content = self.fetch_html(url)
        if html_content:
            return self.convert_to_airform(html_content)
        return None

# Example usage:
if __name__ == "__main__":
    airform = Airform()
    url = "http://example.com"  # Replace with a valid URL
    airform_output = airform.process_url(url)
    if airform_output:
        print(airform_output)