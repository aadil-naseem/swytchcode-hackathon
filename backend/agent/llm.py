import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

llm = ChatOpenAI(
    model=os.getenv("OPENROUTER_MODEL", "openrouter/free"),
    api_key=os.getenv("OPENROUTER_API_KEY", "mock_key"),
    base_url="https://openrouter.ai/api/v1",
    timeout=25.0,
    max_retries=1,
)