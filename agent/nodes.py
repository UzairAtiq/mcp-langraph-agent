import logging
from typing import Callable, Literal
from langchain_groq import ChatGroq
from langgraph.graph import END
from agent.state import MessagesState
from agent.tools import get_langgraph_tools
from config.settings import GROQ_API_KEY, GROQ_MODEL

# configure logger for agent nodes
logger = logging.getLogger("agent_nodes")

# initialize chat groq model instance
llm = ChatGroq(
    model=GROQ_MODEL,
    api_key=GROQ_API_KEY,
    temperature=0.3,
)

# fetch all tools from configured mcp servers
async def get_tools() -> list:
    return await get_langgraph_tools()

# bind mcp tools to the groq llm
def bind_llm_with_tools(tools: list) -> ChatGroq:
    return llm.bind_tools(tools)

# factory to create the agent node closure
def make_agent_node(llm_with_tools) -> Callable:
    async def agent_node(state: MessagesState) -> dict:
        messages = state["messages"]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    return agent_node

# determine routing edge based on tool call presence in latest message
def should_continue(state: MessagesState) -> Literal["tool_node", "__end__"]:
    messages = state["messages"]
    last_message = messages[-1]

    # route to tool_node if llm requested tool calls
    if getattr(last_message, "tool_calls", None):
        return "tool_node"

    # end execution when no further tool calls are requested
    return END