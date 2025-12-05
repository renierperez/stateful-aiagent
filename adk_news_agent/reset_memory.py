import os
from google.cloud import firestore

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT", "autonomous-agent-479317")
COLLECTION_NAME = "news_agent_memory_topics"

def reset_memory():
    print(f"🗑️ Clearing Firestore collection: {COLLECTION_NAME} in project {PROJECT_ID}")
    db = firestore.Client(project=PROJECT_ID)
    collection_ref = db.collection(COLLECTION_NAME)
    docs = collection_ref.stream()
    
    deleted = 0
    for doc in docs:
        doc.reference.delete()
        deleted += 1
        
    print(f"✅ Deleted {deleted} documents.")

if __name__ == "__main__":
    reset_memory()
