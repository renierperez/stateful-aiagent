import logging
import os
from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector
from datetime import datetime, timedelta
import pytz
from google import genai

class NewsMemory:
    def __init__(self, collection_name="news_agent_memory", api_key=None):
        self.db = firestore.Client()
        self.collection_name = collection_name
        self.collection_ref = self.db.collection(self.collection_name)
        self.topics_collection_ref = self.db.collection(f"{self.collection_name}_topics")
        
        if api_key:
            self.genai_client = genai.Client(api_key=api_key)
            logging.info("NewsMemory: GenAI Client inicializado con API Key.")
        else:
            project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
            self.genai_client = genai.Client(vertexai=True, project=project_id, location="us-central1")
            logging.info(f"NewsMemory: GenAI Client inicializado con Vertex AI (Project: {project_id}).")
            
        logging.info(f"Conectado a Firestore, colección: {self.collection_name}")

    def get_recent_summaries(self, days=3):
        """Recupera los resúmenes de los últimos 'days' días."""
        try:
            cutoff_date = datetime.now(pytz.utc) - timedelta(days=days)
            docs = self.collection_ref.where("timestamp", ">=", cutoff_date).order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
            
            summaries = []
            for doc in docs:
                summaries.append(doc.to_dict())
            
            logging.info(f"Recuperados {len(summaries)} resúmenes de los últimos {days} días.")
            return summaries
        except Exception as e:
            logging.error(f"Error al recuperar resúmenes de Firestore: {e}")
            return []

    def save_summary(self, topics_covered, summary_text, news_hash):
        """Guarda un nuevo resumen y sus temas con embeddings en Firestore."""
        try:
            timestamp = datetime.now(pytz.utc)
            
            # 1. Guardar el resumen principal
            data = {
                "timestamp": timestamp,
                "topics_covered": topics_covered,
                "summary_text": summary_text,
                "news_hash": news_hash
            }
            doc_ref = self.collection_ref.add(data)[1] # Get DocumentReference
            summary_id = doc_ref.id
            
            # 2. Generar embeddings y guardar temas individualmente
            if topics_covered:
                for topic in topics_covered:
                    try:
                        result = self.genai_client.models.embed_content(
                            model="text-embedding-004",
                            contents=topic
                        )
                        embedding = result.embeddings[0].values
                        
                        self.topics_collection_ref.add({
                            "topic": topic,
                            "embedding": Vector(embedding),
                            "timestamp": timestamp,
                            "summary_id": summary_id
                        })
                    except Exception as e:
                        logging.error(f"Error al generar embedding para tema '{topic}': {e}")
            
            logging.info("Resumen y temas guardados exitosamente en Firestore.")
            return True
        except Exception as e:
            logging.error(f"Error al guardar resumen en Firestore: {e}")
            return False

    def find_similar_topics(self, topic_text, limit=5, threshold=0.8):
        """Busca temas similares usando búsqueda vectorial en Firestore."""
        try:
            # 1. Generar embedding para el tema de búsqueda
            result = self.genai_client.models.embed_content(
                model="text-embedding-004",
                contents=topic_text
            )
            query_embedding = result.embeddings[0].values
            
            # 2. Realizar búsqueda vectorial en Firestore
            # Nota: Requiere un índice vectorial creado en Firestore.
            # Si no existe, esto fallará. En ese caso, se podría hacer fallback a búsqueda manual (lento).
            from google.cloud.firestore_v1.vector import Vector
            from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
            
            collection_ref = self.topics_collection_ref
            
            # Búsqueda vectorial (KNN)
            results = collection_ref.find_nearest(
                vector_field="embedding",
                query_vector=Vector(query_embedding),
                distance_measure=DistanceMeasure.COSINE,
                limit=limit
            ).stream()
            
            similar_topics = []
            for doc in results:
                # Firestore no devuelve la distancia directamente en el doc de forma fácil en todas las versiones,
                # pero los resultados están ordenados por proximidad.
                data = doc.to_dict()
                similar_topics.append(data["topic"])
            
            return similar_topics
        except Exception as e:
            logging.warning(f"Búsqueda vectorial falló (posiblemente falta índice): {e}")
            return []
