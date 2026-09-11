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


async def get_tools() :

  #getting the tools from multiserverClient
   return await get_langgraph_tools()

def bind_llm_with_tools (tools) :
  #binding the tools with the llm
  llm_with_tools =llm.bind_tools(tools)
  return llm_with_tools


#defining the agent node 
def make_agent_node(llm_with_tools):
    def agent_node(state: MessagesState):
        
        response = llm_with_tools.invoke(state["messages"])

        return {"messages": [response]}
    return agent_node

#defining the should_continue function 
def should_continue(state: MessagesState ) -> str :

  """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

  messages  = state["messages"]
  last_message = messages[-1]

  #if tool call is made then perform an action 
  if last_message.tool_calls :
    return "tool_node"

  #otherwise we stop 
  return END