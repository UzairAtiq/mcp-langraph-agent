from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from agent.state import MessagesState
from agent.nodes import (
    bind_llm_with_tools,
    get_tools,
    make_agent_node,
    should_continue,
)

# compile and return the complete langgraph agent graph
async def build_agent():
    # load tools from all registered mcp servers
    tools = await get_tools()

    # bind tools to llm
    llm_with_tools = bind_llm_with_tools(tools)

    # create agent node handler
    agent_node = make_agent_node(llm_with_tools)

    # construct state graph with message state schema
    agent_builder = StateGraph(MessagesState)

    # register primary agent node and tool execution node
    agent_builder.add_node("agent_node", agent_node)
    agent_builder.add_node("tool_node", ToolNode(tools))

    # define control flow edges
    agent_builder.add_edge(START, "agent_node")
    agent_builder.add_conditional_edges(
        "agent_node",
        should_continue,
        ["tool_node", END],
    )
    agent_builder.add_edge("tool_node", "agent_node")

    # compile and return executable agent
    return agent_builder.compile()
