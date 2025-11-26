import logging

def summarize_articles(articles):
    """
    Takes a list of article dictionaries (with 'title', 'url', 'text').
    Returns a consolidated summary string.
    """
    logging.info("Summarizing articles...")
    summary_parts = []
    
    for i, article in enumerate(articles, 1):
        title = article.get('title', 'Sin título')
        text = article.get('text', '')
        url = article.get('url', '')
        
        # Basic extraction: Take the first 500 characters or first 3 paragraphs
        # This is a heuristic since we don't have a local LLM.
        paragraphs = [p for p in text.split('\n') if len(p) > 50]
        short_summary = " ".join(paragraphs[:2]) # First 2 substantial paragraphs
        
        if len(short_summary) > 600:
            short_summary = short_summary[:600] + "..."
            
        summary_parts.append(f"{i}. {title}\n{short_summary}\nFuente: {url}\n")
        
    consolidated = "RESUMEN DE NOTICIAS - CUBA\n\n" + "\n".join(summary_parts)
    
    # Add a footer explaining this is auto-generated
    consolidated += "\n\n(Este resumen fue generado automáticamente por un agente de Python.)"
    
    return consolidated
