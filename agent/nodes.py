from langgraph.graph import StateGraph, START, END
from typing import Literal
from agent.state import MessagesState
from langchain.messages import SystemMessage
from agent.tools import get_langgraph_tools
from langchain_groq import ChatGroq
from config.settings import GROQ_API_KEY
import asyncio

#setting up the groq model
llm = ChatGroq(
  model="openai/gpt-oss-120b" ,
  api_key=GROQ_API_KEY
    )

#getting the tools from multiserverClient
tools = asyncio.run(get_langgraph_tools())

#binding the tools with the llm
llm_with_tools =llm.bind_tools(tools)

#defining the agent node 
def agent_node(state : MessagesState) :

  messages = state["messages"]
  response = llm_with_tools.invoke(messages)

  return {"messages" : [response]}

#defining the should_continue function 
def should_continue(state: MessagesState ) -> str :

  """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

  messages  = state["messages"]
  last_message = messages[-1]

  #if tool call id made then perform an action 
  if last_message.tool_calls :
    return "tool_node"

  #otherwise we stop 
  return END