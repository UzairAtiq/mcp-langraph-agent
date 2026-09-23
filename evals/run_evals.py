import asyncio
import json
from pathlib import Path
from agent.graph import build_agent
from evals.dataset import TEST_CASES
from evals.judge import judge_response
from observability.tracing import langfuse_handler

# base directory for evaluation artifacts
EVALS_DIR = Path(__file__).resolve().parent
DATASET_OUTPUT_PATH = EVALS_DIR / "dataset.json"

# execute a single evaluation test case through the agent
async def run_single_test(agent, test_case: dict) -> dict:
    # run prompt through compiled agent graph
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": test_case["prompt"]}]},
        config={"callbacks": [langfuse_handler]},
    )

    # extract names of all tools called during execution
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
        "tools_match": actual_tools == test_case["expected_tools"],
    }

# execute full test evaluation suite
async def run_all_tests() -> list[dict]:
    # build agent instance once for test run
    agent = await build_agent()
    results = []

    for test_case in TEST_CASES:
        print(f"running: {test_case['id']}")
        result = await run_single_test(agent, test_case)

        # evaluate execution quality with judge llm
        verdict = await judge_response(result)
        result["judge_score"] = verdict["score"]
        result["judge_reasoning"] = verdict["reasoning"]

        results.append(result)

        status = "pass" if result["tools_match"] else "fail"
        print(f"{status} - expected {result['expected_tools']}, got {result['actual_tools']}")
        print(f"judge: {result['judge_score']} - {result['judge_reasoning']}")

    # persist evaluation results to json file
    DATASET_OUTPUT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"results saved to {DATASET_OUTPUT_PATH}")

    return results

if __name__ == "__main__":
    asyncio.run(run_all_tests())