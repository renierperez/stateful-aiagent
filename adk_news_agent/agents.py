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

    # Combined Agent
    root_agent = LlmAgent(
        name="CubaNewsAgent",
        model=model_name,
        tools=[
            tools.get_past_summaries,
            tools.search_news,
            tools.scrape_content,
            tools.get_economic_indicators,
            tools.send_email,
            tools.save_summary
        ],
        instruction=load_instructions("adk_news_agent/prompts/researcher_instructions.yaml") + "\n" + load_instructions("adk_news_agent/prompts/editor_instructions.yaml")
    )

    return root_agent
