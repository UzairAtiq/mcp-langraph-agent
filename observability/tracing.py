import asyncio
from langfuse.langchain import CallbackHandler
from config.settings import LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL
from agent.graph import build_agent   # your compiled graph

langfuse_handler = CallbackHandler()

