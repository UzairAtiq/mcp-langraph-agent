import asyncio
from langfuse.langchain import CallbackHandler
from config.settings import LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL
from agent.graph import build_agent   # your compiled graph

langfuse_handler = CallbackHandler()

async def main():

    #Building the agent
    agent = await build_agent()

    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": "Look up customer 3 and post their status to Slack"}]},
        config={"callbacks": [langfuse_handler]}
    )
    print(result["messages"])

asyncio.run(main())