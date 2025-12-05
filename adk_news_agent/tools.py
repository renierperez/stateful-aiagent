import os
import logging
from typing import List, Optional, Dict, Any
from news_agent.search import search_news as legacy_search_news
from news_agent.scraper import extract_content as legacy_extract_content
from news_agent.mailer import send_email as legacy_send_email
from news_agent.memory import NewsMemory
from news_agent.reasoning import NewsReasoning
import requests
# Initialize components (assuming env vars are set)
api_key = os.environ.get("GOOGLE_API_KEY")
memory = NewsMemory(api_key=api_key) if api_key else None
reasoning = NewsReasoning(api_key=api_key) if api_key else None

def get_past_summaries(days: int = 3) -> str:
    """Retrieves summaries of news from past days to avoid duplicates."""
    if not memory:
        return "No memory component available."
    summaries = memory.get_recent_summaries(days=days)
    return str(summaries)

def search_news(query: str) -> List[Dict[str, str]]:
    """Searches for news articles based on a query."""
    # Try grounded search first if reasoning is available
    if reasoning:
        results = reasoning.grounded_search([query])
        if results:
            return results
    # Fallback to legacy search
    return legacy_search_news(query)

def scrape_content(url: str) -> str:
    """Extracts text content from a given URL."""
    content = legacy_extract_content(url) or ""
    # Truncate content to avoid context overflow (approx 5000 chars)
    return content[:5000] + "... (truncated)" if len(content) > 5000 else content
def get_google_trends(region: str = 'US', limit: int = 5) -> str:
    """Gets top trending terms related to 'cuba' from Google Trends using SerpApi.
    Args:
        region: Not used in this version, focused on 'cuba' query.
        limit: Number of top terms to return.
    """
    print(f"DEBUG: Calling get_google_trends with region={region}, limit={limit}")
    logging.info(f"Calling get_google_trends with region={region}, limit={limit}")
    
    api_key = os.environ.get("CUBA_NEWS_SERPAPI_KEY")
    if not api_key:
        return "Error: CUBA_NEWS_SERPAPI_KEY not set."

    try:
        # SerpApi Google Trends parameters
        params = {
            "engine": "google_trends",
            "q": "cuba",
            "data_type": "RELATED_QUERIES",
            "api_key": api_key
        }
        
        response = requests.get("https://serpapi.com/search", params=params)
        data = response.json()
        
        if "error" in data:
            return f"SerpApi Error: {data['error']}"

        results_parts = []
        
        # Process Related Queries (Rising)
        if "related_queries" in data:
            rising_queries = data["related_queries"].get("rising", [])
            if rising_queries:
                top_queries = [item["query"] for item in rising_queries[:limit]]
                results_parts.append(f"Rising queries: {', '.join(top_queries)}")
            
            top_queries = data["related_queries"].get("top", [])
            if top_queries:
                top_terms = [item["query"] for item in top_queries[:limit]]
                results_parts.append(f"Top queries: {', '.join(top_terms)}")

        if results_parts:
            result = " | ".join(results_parts)
            print(f"DEBUG: get_google_trends result: {result}")
            logging.info(f"get_google_trends result: {result}")
            return f"Google Trends for Cuba: {result}"
        
        return "No trending data found for 'cuba'."

    except Exception as e:
        print(f"DEBUG: SerpApi Google Trends failed: {str(e)}")
        logging.error(f"SerpApi Google Trends failed: {str(e)}")
        return f"Error fetching Google Trends via SerpApi: {str(e)}"

def get_economic_indicators() -> str:
    """Gets current economic indicators for Cuba."""
    # Try Marti
    text = legacy_extract_content("https://www.martinoticias.com/tasa-de-cambio-de-moneda-cuba-hoy")
    if text and ("USD" in text or "EUR" in text):
        return text
    
    # Try El Toque
    text = legacy_extract_content("https://eltoque.com/tasas-de-cambio-de-moneda-en-cuba-hoy")
    if text and ("USD" in text or "EUR" in text):
        return text
    
    # Try CambioCuba (simplified for tool output, might need OCR or just URL)
    return "Check https://wa.cambiocuba.money/trmi.png for latest rates."

def send_email(subject: str, body: str, to_email: Optional[str] = None, bcc_emails: Optional[List[str]] = None) -> str:
    """Sends an email with the given subject and body. If to_email is not provided, uses GMAIL_USER."""
    user_email = os.environ.get("GMAIL_USER")
    password = os.environ.get("GMAIL_PASSWORD")
    
    if not user_email or not password:
        return "Error: GMAIL_USER or GMAIL_PASSWORD not set."
    
    recipient = to_email or user_email
    
    # Handle BCC from env if not provided
    if bcc_emails is None:
        bcc_str = os.environ.get("BCC_EMAILS")
        if bcc_str:
            bcc_emails = [email.strip() for email in bcc_str.split(',')]
    
    success = legacy_send_email(user_email, password, subject, body, to_email=recipient, bcc_emails=bcc_emails, is_html=True)
    return "Email sent successfully." if success else "Failed to send email."

def save_summary(topics: List[str], summary: str, news_hash: str) -> str:
    """Saves the generated summary to memory."""
    if not memory:
        return "No memory component available."
    memory.save_summary(topics, summary, news_hash)
    return "Summary saved to memory."
