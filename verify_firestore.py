import os
from google.cloud import firestore
from datetime import datetime, timedelta
import pytz

def verify_firestore():
    db = firestore.Client()
    collection_ref = db.collection("news_agent_memory")
    
    print("Querying Firestore for recent summaries...")
    docs = collection_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).stream()
    
    found = False
    for doc in docs:
        found = True
        data = doc.to_dict()
        print(f"Document ID: {doc.id}")
        print(f"Timestamp: {data.get('timestamp')}")
        print(f"Topics Covered: {data.get('topics_covered')}")
        print(f"Summary Snippet: {str(data.get('summary_text'))[:100]}...")
    
    if not found:
        print("No documents found in news_agent_memory.")

if __name__ == "__main__":
    verify_firestore()
