import os
import logging
from typing import List, Optional, Dict, Any
from news_agent.search import search_news as legacy_search_news
from news_agent.scraper import extract_content as legacy_extract_content
from news_agent.mailer import send_email as legacy_send_email
from news_agent.memory import NewsMemory
from news_agent.reasoning import NewsReasoning
import requests

from pytrends.request import TrendReq
from google.cloud import bigquery
import requests

# Initialize components (assuming env vars are set)
api_key = os.environ.get("GOOGLE_API_KEY")
memory = NewsMemory(api_key=api_key) if api_key else None
reasoning = NewsReasoning(api_key=api_key) if api_key else None
bq_client = bigquery.Client() if os.environ.get("GOOGLE_CLOUD_PROJECT") else None

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

def get_google_trends(region: str = 'US', limit: int = 5) -> str:
    """Gets top trending terms related to 'cuba' from Google Trends.
    Args:
        region: Not used in this version, focused on 'cuba' query.
        limit: Number of top terms to return.
    """
    print(f"DEBUG: Calling get_google_trends with region={region}, limit={limit}")
    logging.info(f"Calling get_google_trends with region={region}, limit={limit}")
    try:
        # Initialize pytrends with English (US) and Chile timezone (approx)
        pytrends = TrendReq(hl='en-us', tz=180) # tz=180 for UTC-3
        # Use topic ID for Cuba: /m/0d04z6
        kw_list = ["/m/0d04z6"] 
        
        # Build payload for last 4 hours
        pytrends.build_payload(kw_list, cat=0, timeframe='now 4-H', geo='', gprop='')
        
        # Get related queries and topics
        related_queries = pytrends.related_queries()
        related_topics = pytrends.related_topics()
        
        results_parts = []
        
        # Process Related Queries
        if '/m/0d04z6' in related_queries and related_queries['/m/0d04z6']['top'] is not None:
            top_queries_df = related_queries['/m/0d04z6']['top']
            if not top_queries_df.empty:
                top_queries = top_queries_df['query'].head(limit).tolist()
                results_parts.append(f"Top related queries: {', '.join(top_queries)}")
        
        # Process Related Topics
        if '/m/0d04z6' in related_topics and related_topics['/m/0d04z6']['top'] is not None:
            top_topics_df = related_topics['/m/0d04z6']['top']
            if not top_topics_df.empty:
                # Top topics usually have 'topic_title' and 'topic_type'
                top_topics = top_topics_df['topic_title'].head(limit).tolist()
                results_parts.append(f"Top related topics: {', '.join(top_topics)}")
        
        if results_parts:
            result = " | ".join(results_parts)
            print(f"DEBUG: get_google_trends result: {result}")
            logging.info(f"get_google_trends result: {result}")
            return f"Google Trends for Cuba (last 4h): {result}"
        
        # Fallback to general trends if no data found
        print("DEBUG: No data found for Cuba topic, falling back to BigQuery.")
        logging.info("No data found for Cuba topic, falling back to BigQuery.")
        return get_google_trends_bigquery(region='US', limit=limit)
    except Exception as e:
        # Fallback to BigQuery on any error (including 429)
        print(f"DEBUG: Pytrends failed: {str(e)}. Falling back to BigQuery.")
        logging.warning(f"Pytrends failed: {str(e)}. Falling back to BigQuery.")
        return get_google_trends_bigquery(region='US', limit=limit)

def get_google_trends_bigquery(region: str = 'US', limit: int = 5) -> str:
    """Fallback to BigQuery for general trending terms."""
    print(f"DEBUG: Calling get_google_trends_bigquery with region={region}, limit={limit}")
    logging.info(f"Calling get_google_trends_bigquery with region={region}, limit={limit}")
    if not bq_client:
        return "BigQuery client not initialized. Cannot access Google Trends."
    
    query = f"""
        SELECT term, rank
        FROM `bigquery-public-data.google_trends.top_terms`
        WHERE refresh_date = (SELECT MAX(refresh_date) FROM `bigquery-public-data.google_trends.top_terms`)
        AND dma_name IS NULL -- Global/Country level, not city level
        AND country_code = '{region}'
        ORDER BY rank ASC
        LIMIT {limit}
    """
    try:
        query_job = bq_client.query(query)
        results = query_job.result()
        trends = [row.term for row in results]
        if not trends:
            return f"No trending terms found for region {region}."
        result = f"Top trending terms in {region} (Fallback): {', '.join(trends)}"
        print(f"DEBUG: get_google_trends_bigquery result: {result}")
        logging.info(f"get_google_trends_bigquery result: {result}")
        return result
    except Exception as e:
        print(f"DEBUG: BigQuery failed: {str(e)}")
        logging.error(f"BigQuery failed: {str(e)}")
        return f"Error fetching Google Trends via BigQuery: {str(e)}"

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
