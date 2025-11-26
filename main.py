import logging
import getpass
import hashlib
import os
from dotenv import load_dotenv
from news_agent.search import search_news
from news_agent.scraper import extract_content
from news_agent.mailer import send_email
from news_agent.memory import NewsMemory
from news_agent.reasoning import NewsReasoning

def generate_hash(articles):
    combined = "".join([a.get('title', '') for a in articles])
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()

def main():
    # Load environment variables
    load_dotenv()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=== Agente de Noticias de Cuba (Stateful) ===")
    print("Este agente utilizará memoria persistente y IA para buscar noticias.")
    
    # 1. Initialize Memory
    api_key = os.environ.get("GOOGLE_API_KEY")
    
    try:
        memory = NewsMemory(api_key=api_key)
        reasoning = NewsReasoning(api_key=api_key)
    except Exception as e:
        logging.error(f"Error al inicializar componentes: {e}")
        return

    # 3. Retrieve Context
    past_summaries = memory.get_recent_summaries(days=3)
    
    # 4. Generate Queries
    queries = reasoning.generate_search_queries(past_summaries)
    
    # 5. Search News
    logging.info("Buscando noticias...")
    all_results = reasoning.grounded_search(queries)
    
    if not all_results:
        logging.warning("Grounding no devolvió resultados, intentando búsqueda tradicional...")
        all_results = []
        for query in queries:
            res = search_news(query)
            all_results.extend(res)
    
    if not all_results:
        logging.warning("No se encontraron noticias.")
        # Continue to allow economic indicators and analysis
    
    # 6. Filter Redundant Articles
    filtered_results = reasoning.filter_articles(all_results, memory) if all_results else []
    
    if not filtered_results and all_results:
        logging.warning("Todas las noticias encontradas eran redundantes.")
        # Continue to allow economic indicators and analysis
    
    # 7. Scrape Content
    articles_data = []
    for res in filtered_results:
        url = res['url']
        text = extract_content(url)
        if text:
            res['text'] = text
            articles_data.append(res)
    
    if not articles_data:
        logging.warning("No se pudo extraer contenido de nuevas noticias. Se continuará para actualizar indicadores y análisis.")
    
    # 8. Scrape Economic Indicators (Martí Noticias)
    logging.info("Obteniendo indicadores económicos de Martí Noticias...")
    marti_text = extract_content("https://www.martinoticias.com/tasa-de-cambio-de-moneda-cuba-hoy")
    
    economic_data = marti_text
    
    # Fallback to El Toque if Martí fails or doesn't have data
    if not marti_text or ("USD" not in marti_text and "EUR" not in marti_text):
        logging.info("Martí Noticias no proporcionó datos claros, intentando con El Toque...")
        el_toque_text = extract_content("https://eltoque.com/tasas-de-cambio-de-moneda-en-cuba-hoy")
        economic_data = el_toque_text
        
        if not el_toque_text or ("USD" not in el_toque_text and "EUR" not in el_toque_text):
            logging.info("El Toque tampoco proporcionó datos, intentando con CambioCuba (imagen)...")
            import requests
            try:
                img_response = requests.get("https://wa.cambiocuba.money/trmi.png", timeout=10)
                if img_response.status_code == 200:
                    economic_data = img_response.content # Pass bytes
                    logging.info("Imagen de CambioCuba descargada exitosamente.")
                else:
                    logging.warning(f"No se pudo descargar imagen de CambioCuba: {img_response.status_code}")
            except Exception as e:
                logging.error(f"Error al descargar imagen de CambioCuba: {e}")

    # 9. Summarize via Reasoning
    summary, topics = reasoning.summarize_articles(articles_data, past_summaries, economic_data=economic_data)
    # 10. Send Email
    print("\n--- Resumen Generado (HTML) ---\n")
    print(f"Temas: {', '.join(topics)}")
    print(summary)
    print("\n------------------------\n")
    
    # Check for non-interactive mode (e.g., Cloud Run)
    non_interactive = os.environ.get("NON_INTERACTIVE", "false").lower() == "true"
    
    if non_interactive:
        send_email_choice = 's'
    else:
        send_email_choice = input("¿Deseas enviar este resumen por correo? (s/n): ").lower()
    
    if send_email_choice == 's':
        email = os.environ.get("GMAIL_USER")
        password = os.environ.get("GMAIL_PASSWORD")
        
        if not email or not password:
            if non_interactive:
                logging.error("GMAIL_USER o GMAIL_PASSWORD no configurados en modo no interactivo. Saliendo.")
                return
            else:
                email = input("Introduce tu correo de Gmail: ")
                password = getpass.getpass("Introduce tu contraseña de aplicación de Gmail: ")
        
        bcc_emails_str = os.environ.get("BCC_EMAILS", "")
        # Use semicolon as delimiter to avoid gcloud issues with commas
        bcc_emails = [e.strip() for e in bcc_emails_str.split(";")] if bcc_emails_str else None
        
        logging.info(f"Sending email to {email} (BCC: {bcc_emails})...")
        news_hash = generate_hash(articles_data) # Generate hash before sending email
        if send_email(email, password, "Resumen Diario: Cuba", summary, bcc_emails=bcc_emails, is_html=True):
            print("¡Correo enviado correctamente!")
            # 11. Save to Memory
            memory.save_summary(topics, summary, news_hash)
        else:
            print("Error al enviar el correo.")
    else:
        print("Operación cancelada por el usuario. No se guardó en memoria.")

if __name__ == "__main__":
    main()
