from agent.state import MessagesState
from langgraph.graph import StateGraph,START,END
from langgraph.prebuilt import ToolNode
from agent.nodes import get_tools
from agent.nodes import should_continue
from agent.nodes import bind_llm_with_tools
from agent.nodes import make_agent_node
from IPython.display import Image, display
import asyncio


async def build_agent() :
  #getting the tools 
  tools = await get_tools()

  #binding the tools with the llm 
  llm_with_tools = bind_llm_with_tools(tools)

  #creating the agent
  agent_node = make_agent_node(llm_with_tools)


  agent_builder = StateGraph(MessagesState) 

  #Adding nodes 
  agent_builder.add_node("agent_node" , agent_node )

  agent_builder.add_node("tool_node" , ToolNode(tools) )

  # Add edges to connect nodes
  agent_builder.add_edge(START, "agent_node")
  agent_builder.add_conditional_edges(
      "agent_node",
      should_continue,
      ["tool_node", END]
  )
  agent_builder.add_edge("tool_node", "agent_node")

  # Compile the agent
  agent = agent_builder.compile()
  return agent

