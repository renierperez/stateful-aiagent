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
    return legacy_extract_content(url) or ""

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
