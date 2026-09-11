import asyncio
import json
from agent.graph import build_agent
from observability.tracing import langfuse_handler
from evals.dataset import TEST_CASES
from evals.judge import judge_response


async def run_single_test(agent, test_case):
    # run one prompt through the agent
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": test_case["prompt"]}]},
        config={"callbacks": [langfuse_handler]}
    )

    # get list of tools that were actually called
    actual_tools = []
    for msg in result["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for call in msg.tool_calls:
                actual_tools.append(call["name"])

    final_answer = result["messages"][-1].content

    return {
        "id": test_case["id"],
        "prompt": test_case["prompt"],
        "expected_tools": test_case["expected_tools"],
        "actual_tools": actual_tools,
        "final_answer": final_answer,
        "tools_match": actual_tools == test_case["expected_tools"]
    }


async def run_all_tests():
    # build agent once, reuse for all tests
    agent = await build_agent()
    results = []

    for test_case in TEST_CASES:
        print(f"running: {test_case['id']}")
        result = await run_single_test(agent, test_case)

        # ask the judge to score this result
        verdict = await judge_response(result)
        result["judge_score"] = verdict["score"]
        result["judge_reasoning"] = verdict["reasoning"]

        results.append(result)

        # simple pass or fail print
        status = "pass" if result["tools_match"] else "fail"
        print(f"{status} - expected {result['expected_tools']}, got {result['actual_tools']}")
        print(f"judge: {result['judge_score']} - {result['judge_reasoning']}")

    # write results to a json file
    with open("/Users/uzair/Developer/mcp-langraph-agent/evals/dataset.json", "w") as f:
        json.dump(results, f, indent=2)

    print("results saved to evals/dataset.json")

    return results


if __name__ == "__main__":
    asyncio.run(run_all_tests())