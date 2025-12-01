import os
from google.adk.agents import LlmAgent, SequentialAgent
from adk_news_agent import tools
import yaml

def load_instructions(path):
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
        return data['instructions']

def create_agents():
    # Model configuration
    model_name = os.environ.get("MODEL_NAME", "gemini-2.5-pro")

    # Load prompts
    instructions_path = os.path.join(os.path.dirname(__file__), 'prompts', 'agent_instructions.yaml')
    persona_path = os.path.join(os.path.dirname(__file__), 'prompts', 'persona.yaml')
    rules_path = os.path.join(os.path.dirname(__file__), 'prompts', 'rules.yaml')
    
    with open(instructions_path, 'r') as f:
        instructions_data = yaml.safe_load(f)
    with open(persona_path, 'r') as f:
        persona_data = yaml.safe_load(f)
    with open(rules_path, 'r') as f:
        rules_data = yaml.safe_load(f)
        
    combined_instructions = f"{persona_data['persona']}\n\n{rules_data['rules']}\n\n{instructions_data['instructions']}"

    # Combined Agent
    root_agent = LlmAgent(
        name="CubaNewsAgent",
        model=model_name,
        tools=[
            tools.get_past_summaries,
            tools.search_news,
            tools.scrape_content,
            tools.get_economic_indicators,
            tools.get_google_trends,
            tools.send_email,
            tools.save_summary
        ],
        instruction=load_instructions("adk_news_agent/prompts/agent_instructions.yaml")
    )

    return root_agent
