from duckduckgo_search import DDGS
import logging

def search_news(query="actualidad en Cuba", max_results=5):
    """
    Searches for the latest news using DuckDuckGo.
    Returns a list of dictionaries with 'title', 'href', and 'body'.
    """
    logging.info(f"Searching for: {query}")
    results = []
    try:
        with DDGS() as ddgs:
            # backend="news" is specifically for news
            news_gen = ddgs.news(query, region="wt-wt", safesearch="off", max_results=max_results)
            for r in news_gen:
                results.append({
                    "title": r.get("title"),
                    "url": r.get("url") or r.get("href"), # DDGS keys might vary slightly by version
                    "snippet": r.get("body")
                })
    except Exception as e:
        logging.error(f"Error during search: {e}")
    
    return results

if __name__ == "__main__":
    # Simple test
    logging.basicConfig(level=logging.INFO)
    print(search_news())
