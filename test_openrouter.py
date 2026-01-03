import os
from dotenv import load_dotenv, find_dotenv
from agents import Agent, RunConfig, AsyncOpenAI, OpenAIChatCompletionsModel, Runner

load_dotenv(find_dotenv())

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    print("ERROR: OPENROUTER_API_KEY not found in .env file")
    print("Please add your OpenRouter API key to continue")
    exit(1)

print(f"API Key found: {OPENROUTER_API_KEY[:10]}..." if OPENROUTER_API_KEY else "No API key")

# Configure OpenRouter
provider = AsyncOpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

model = OpenAIChatCompletionsModel(
    model="openai/gpt-4o-mini",
    openai_client=provider,
)

run_config = RunConfig(
    model=model,
    model_provider=provider,
    tracing_disabled=True,
)

agent = Agent(
    instructions="You are a helpful assistant.",
    name="Test Agent",
)

print("\nTesting OpenRouter API connection...")
print("Model: openai/gpt-4o-mini")
print("Base URL: https://openrouter.ai/api/v1\n")

async def test():
    try:
        result = await Runner.run(
            agent,
            input="Say 'OpenRouter is working!' in a single sentence.",
            run_config=run_config,
        )
        print(f"[SUCCESS]: {result.final_output}")
        return True
    except Exception as e:
        print(f"[ERROR]: {e}")
        return False

import asyncio
success = asyncio.run(test())

if success:
    print("\nOpenRouter integration is working correctly!")
else:
    print("\nOpenRouter integration failed. Please check your API key and try again.")
