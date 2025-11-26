import requests
from bs4 import BeautifulSoup
import logging

def extract_content(url):
    """
    Fetches the URL and extracts the main text content.
    Returns a dictionary with 'text' and 'url'.
    """
    logging.info(f"Scraping: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
            
        # Get text
        text = soup.get_text(separator='\n')
        
        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        logging.error(f"Failed to scrape {url}: {e}")
        return ""

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Test with a dummy URL if needed, or just run main
    pass
