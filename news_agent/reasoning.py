import logging
import os
from google import genai
from google.genai import types
import json

class NewsReasoning:
    def __init__(self, model_name="gemini-1.5-flash", api_key=None):
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        api_key = os.environ.get("GOOGLE_API_KEY")
        
        if api_key:
            # Use Google AI Studio
            self.client = genai.Client(api_key=api_key)
            self.model_name = os.environ.get("GOOGLE_MODEL_NAME", "gemini-2.0-flash-exp") # Default to a known working model for AI Studio
            logging.info(f"Google Gen AI SDK inicializado con AI Studio. Modelo: {self.model_name}")
        else:
            # Use Vertex AI
            if not project_id:
                logging.warning("GOOGLE_CLOUD_PROJECT no está configurada.")
            self.client = genai.Client(vertexai=True, project=project_id, location=location)
            self.model_name = model_name
            logging.info(f"Google Gen AI SDK inicializado con Vertex AI. Modelo: {self.model_name}")

    def generate_search_queries(self, past_summaries):
        """Genera 3 términos de búsqueda basados en el contexto pasado."""
        import datetime
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        context_text = "\n".join([f"- {s['timestamp']}: {', '.join(s['topics_covered'])}" for s in past_summaries])
        
        prompt = f"""
        Eres un agente de noticias experto en Cuba. Hoy es {current_date}.
        Basado en los siguientes temas cubiertos en los últimos días:
        {context_text}
        
        Genera 3 términos de búsqueda (queries) para encontrar noticias nuevas.
        - **IMPORTANTE:** Solo busca noticias publicadas hoy o ayer ({current_date}).
        - Usa términos como 'hoy', 'última hora', o el año actual '2025' para asegurar frescura.
        - No limites las búsquedas a un solo dominio usando 'site:'. Usa términos generales para obtener resultados de diversas fuentes.
        - Evita temas que ya estén cerrados o repetidos sin nueva información.
        
        Responde únicamente con un objeto JSON que contenga una lista de strings llamada 'queries'.
        Ejemplo: {{"queries": ["apagones cuba hoy", "relaciones cuba estados unidos", "economía cuba 2025"]}}
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            # Basic JSON extraction from response text
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(text)
            queries = data.get("queries", ["actualidad Cuba hoy", "noticias Cuba última hora", "Cuba 2025"])
            logging.info(f"Queries generadas: {queries}")
            return queries[:3]
        except Exception as e:
            logging.error(f"Error al generar queries: {e}")
            return ["actualidad Cuba hoy", "noticias Cuba última hora", "Cuba 2025"]

    def grounded_search(self, queries):
        """Realiza búsquedas usando Vertex AI Grounding con Google Search."""
        all_results = []
        for query in queries:
            try:
                # Grounding with Google Search
                # Note: This requires the model to support grounding, e.g., gemini-1.5-pro or gemini-1.5-flash
                # and the client must be initialized with Vertex AI or have access to Google Search tool.
                
                # For AI Studio, grounding is not directly available via the same API yet, 
                # but we can simulate it or use the model's knowledge if it's fresh.
                # However, the user wants Vertex AI Grounding.
                
                # If using AI Studio, we might need a different approach or just rely on its fresh knowledge.
                # Given the constraints, I will implement it using the Google Search tool if available, 
                # or fallback to standard generation if not.
                
                from google.genai.types import Tool, GoogleSearch
                
                google_search_tool = Tool(google_search=GoogleSearch())
                
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=f"Busca noticias recientes sobre: {query}. Proporciona una lista de URLs de fuentes confiables.",
                    config={
                        'tools': [google_search_tool],
                    }
                )
                
                # Extract URLs from grounding metadata or text
                # This is a bit tricky as the structure depends on the response.
                # We will look for URLs in the text as a fallback.
                import re
                urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', response.text)
                
                for url in urls:
                    # Clean URL
                    url = url.strip().rstrip(').,')
                    if url not in [r['url'] for r in all_results]:
                        all_results.append({
                            'title': f"Resultado de Grounding para {query}",
                            'url': url,
                            'snippet': response.text[:200] # Use part of response as snippet
                        })
                
                logging.info(f"Grounding para '{query}' encontró {len(urls)} URLs.")
                
            except Exception as e:
                logging.warning(f"Grounding falló para '{query}': {e}")
                # Fallback to standard search is handled in main.py if this returns empty
        
        return all_results

    def filter_articles(self, articles, memory):
        """Filtra artículos que sean semánticamente redundantes usando memoria vectorial."""
        if not articles:
            return []
        
        filtered_articles = []
        for article in articles:
            title = article.get('title', '')
            snippet = article.get('snippet', '')
            
            # 1. Buscar temas similares en memoria vectorial
            similar_topics = memory.find_similar_topics(title, limit=3)
            
            if similar_topics:
                logging.info(f"Temas similares encontrados para '{title}': {similar_topics}")
                # 2. Usar LLM para decidir si es redundante basado en temas similares
                prompt = f"""
                Analiza si la siguiente noticia es redundante con respecto a los temas ya cubiertos recientemente.
                
                Temas cubiertos recientemente (similares): {', '.join(similar_topics)}
                
                Nueva noticia:
                Título: {title}
                Resumen: {snippet}
                
                ¿Es esta noticia nueva y aporta información relevante, o es repetida/redundante con los temas cubiertos?
                Responde únicamente con 'NUEVA' o 'REPETIDA'.
                """
                
                try:
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt
                    )
                    result = response.text.strip().upper()
                    if "NUEVA" in result:
                        filtered_articles.append(article)
                    else:
                        logging.info(f"Artículo filtrado por redundancia semántica: {title}")
                except Exception as e:
                    logging.error(f"Error al filtrar artículo: {e}")
                    filtered_articles.append(article) # Keep it if error
            else:
                # No hay temas similares, es nueva
                filtered_articles.append(article)
        
        return filtered_articles

    def summarize_articles(self, articles_data=None, past_summaries=None, economic_data=None):
        """Genera un resumen consolidado de los artículos en formato HTML."""
        articles_text = ""
        if articles_data:
            for i, art in enumerate(articles_data):
                articles_text += f"--- Articulo {i+1} ---\n"
                articles_text += f"Título: {art.get('title')}\n"
                articles_text += f"Fuente: {art.get('url')}\n"
                articles_text += f"Contenido: {art.get('text')[:2000]}\n\n" # Limit text per article
        else:
            articles_text = "No se encontraron nuevas noticias relevantes hoy."
        
        context_text = ""
        if past_summaries:
            context_text = "\n".join([f"- {s['timestamp']}: {', '.join(s['topics_covered'])}" for s in past_summaries])

        economic_section = ""
        contents = []
        
        if economic_data:
            if isinstance(economic_data, bytes):
                # Handle image data
                from google.genai import types
                img_part = types.Part.from_bytes(data=economic_data, mime_type="image/png")
                contents.append(img_part)
                economic_section = "\n[Imagen de Tasas de Cambio adjunta]\n"
            else:
                # Handle text data
                economic_section = f"\nDatos de Tasas de Cambio (El Toque):\n{economic_data[:2000]}\n"

        prompt = f"""
        Eres un periodista internacional experto en política y economía de Cuba.
        Crea un boletín de noticias profesional en formato HTML.
        
        Contexto de días anteriores:
        {context_text}
        
        Noticias de hoy:
        {articles_text}
        {economic_section}
        
        Instrucciones para el formato HTML (Sigue este estilo EXACTAMENTE):
        1.  **Estilo General:** Fuente sans-serif (Helvetica, Arial), fondo blanco, ancho máximo 800px.
        2.  **Título:** "🇨🇺 Resumen Diario de Cuba" en azul oscuro, con una línea gruesa debajo.
        3.  **Análisis del Editor:** Un cuadro con fondo gris claro (`#f4f4f4`), bordes redondeados, texto en cursiva. Título "Análisis del Editor:" en negrita.
        4.  **Noticias:** Título "Las 5 Noticias Más Importantes del Día" en azul. Lista numerada. Cada ítem con:
            - Título en negrita.
            - Breve descripción (si hay).
            - Enlace "Leer más →" en color rojo/naranja, abriendo en nueva pestaña.
        5.  **Indicadores Económicos:** Si hay datos, crea una sección similar a las noticias o una tabla sencilla, antes del pie de página.
        6.  **Pie de página:** Centrado, color gris, texto "Generado por Google AI ({self.model_name}) - 2025".
        
        Contenido:
        - Si hay noticias nuevas: Analiza los hechos del día, comparando con días anteriores. Contrasta fuentes oficiales e internacionales.
        - Si NO hay noticias nuevas: Indica que la situación se mantiene estable.
        3. **Sección de Economía (OBLIGATORIA)**: Incluye siempre una sección con las tasas de cambio, usando los datos proporcionados. Si no hay datos, indica que no están disponibles hoy, pero mantén la sección.
        
        Usa un tono profesional, analítico y objetivo.
        
        Datos de Noticias:
        {articles_text}
        
        {economic_section}
        
        Resúmenes Recientes (Contexto):
        {context_text}
        
        Responde únicamente con un objeto JSON:
        {{
            "summary_html": "contenido HTML aquí...",
            "topics": ["tema1", "tema2", "tema3"]
        }}
        """
        contents.append(prompt)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(text)
            return data.get("summary_html", ""), data.get("topics", [])
        except Exception as e:
            logging.error(f"Error al resumir: {e}")
            return "Error al generar el resumen.", []
