import os
import logging
import asyncio
from dotenv import load_dotenv
from adk_news_agent.agents import create_agents
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

async def run_agent():
    print("Iniciando agente...")
    root_agent = create_agents()
    
    # Setup Runner and Session Service
    session_service = InMemorySessionService()
    # Create session
    await session_service.create_session(
        app_name="agents",
        user_id="test_user",
        session_id="test_session"
    )
    runner = Runner(
        agent=root_agent,
        app_name="agents", # Match expected app name to avoid warning
        session_service=session_service
    )
    
    print("Enviando mensaje al agente...")
    # Send message and handle events
    async for event in runner.run_async(
        user_id="test_user",
        session_id="test_session",
        new_message=types.Content(
            role="user",
            parts=[types.Part(text="Genera el resumen de noticias de hoy.")]
        )
    ):
        # ADK events can be different types, we are interested in the final response or intermediate steps
        # For now, let's print the event to see what we get
        print(f"Evento: {event}")
        # If event has a text attribute, it might be the response
        if hasattr(event, 'text'):
            print(f"Texto: {event.text}")
    
    return "Ejecución completada"

def main():
    # Load environment variables
    load_dotenv()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=== Agente de Noticias de Cuba (ADK) ===")
    
    # Create and run the agent
    try:
        result = asyncio.run(run_agent())
        print("\n--- Resultado del Agente ---\n")
        print(result)
        print("\n--------------------------\n")
    except Exception as e:
        logging.error(f"Error al ejecutar el agente: {e}")
        # In a real scenario, we might want to print the stack trace
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
