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


if __name__ == "__main__":
    import asyncio
    from langchain_core.messages import HumanMessage
    from observability.tracing import langfuse_handler

    # execute agent with user prompt and langfuse tracing
    async def run_agent_interactive():
        print("Initializing LangGraph Agent with MCP tools and Langfuse tracing...")
        agent = await build_agent()

        prompt = (
            "Create an engaging LinkedIn post about building production-grade AI agents "
            "with Model Context Protocol (MCP), send it to Slack for user approval, and wait for the decision."
        )
        print(f"\n👤 User Prompt:\n{prompt}\n")

        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=prompt)]},
            config={"callbacks": [langfuse_handler]},
        )

        final_response = result["messages"][-1].content
        print(f"\nAgent Final Response:\n{final_response}\n")

    asyncio.run(run_agent_interactive())

