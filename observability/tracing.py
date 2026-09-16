from langfuse.langchain import CallbackHandler
from config.settings import LANGFUSE_BASE_URL, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY

# initialize langfuse callback handler for langchain and langgraph agents
langfuse_handler = CallbackHandler()
