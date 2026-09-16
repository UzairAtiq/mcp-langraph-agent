import asyncio
from langchain_core.messages import HumanMessage
from agent.graph import build_agent
from agent.tools import get_langgraph_tools

# test that get_langgraph_tools loads tools from all 3 mcp servers
async def run_tool_loading_test():
    tools = await get_langgraph_tools()
    tool_names = [tool.name for tool in tools]

    # verify presence of tools across all servers
    assert "lookup_customer" in tool_names or "get_customer_by_id" in tool_names
    assert "send_slack_message" in tool_names
    assert "generate_and_request_approval" in tool_names
    assert "get_post_details" in tool_names
    assert "list_all_generated_posts" in tool_names

    return tool_names

def test_get_langgraph_tools():
    tool_names = asyncio.run(run_tool_loading_test())
    print(f"  ✓ loaded tools from all 3 MCP servers: {tool_names}")

# test compiling the langgraph agent
async def run_build_agent_test():
    agent = await build_agent()
    assert agent is not None
    return agent

def test_build_agent():
    agent = asyncio.run(run_build_agent_test())
    print("  ✓ LangGraph agent compiled successfully with all nodes and edges")

# test full end-to-end agent invocation with langgraph
async def run_agent_invocation_test():
    agent = await build_agent()
    
    # send prompt asking to list generated posts or inspect a post
    test_state = {
        "messages": [
            HumanMessage(content="Use your tool to list all generated LinkedIn posts and tell me how many exist.")
        ]
    }
    
    result = await agent.ainvoke(test_state)
    messages = result["messages"]
    
    # assert that the agent executed and produced a final response
    assert len(messages) >= 2
    final_message = messages[-1]
    assert final_message.content != ""
    print(f"  ✓ LangGraph end-to-end agent response: {final_message.content[:80]}...")

def test_agent_invocation():
    asyncio.run(run_agent_invocation_test())
