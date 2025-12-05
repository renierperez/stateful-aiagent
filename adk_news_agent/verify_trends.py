import os
import logging
from adk_news_agent.tools import get_google_trends

# Configure logging
logging.basicConfig(level=logging.INFO)

def test_google_trends():
    print("Testing get_google_trends with SerpApi...")
    
    # Ensure CUBA_NEWS_SERPAPI_KEY is set (you might need to set this in your env)
    if not os.environ.get("CUBA_NEWS_SERPAPI_KEY"):
        print("WARNING: CUBA_NEWS_SERPAPI_KEY not set. Test might fail.")
    
    try:
        result = get_google_trends(limit=5)
        print("\nResult:")
        print(result)
        
        if "Error" in result:
            print("\n❌ Test Failed")
        else:
            print("\n✅ Test Passed")
            
    except Exception as e:
        print(f"\n❌ Exception: {e}")

if __name__ == "__main__":
    test_google_trends()
