import json
from langchain_groq import ChatGroq
from config.settings import GROQ_API_KEY

# initialize standalone llm instance for evaluation
judge_llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=GROQ_API_KEY,
)

# evaluate single agent execution result against expected behavior
async def judge_response(result: dict) -> dict:
    # construct evaluation prompt from test execution details
    judge_prompt = f"""
you are evaluating an ai agent's response.

user request: {result['prompt']}
expected tools: {result['expected_tools']}
tools actually called: {result['actual_tools']}
agent's final answer: {result['final_answer']}

decide if the agent behaved correctly.
respond only in this json format, nothing else:
{{"score": "pass" or "fail", "reasoning": "one short sentence"}}
"""

    # request evaluation verdict from judge model
    response = await judge_llm.ainvoke(judge_prompt)

    # parse json structure from response text
    try:
        clean_text = response.content.replace("```json", "").replace("```", "").strip()
        verdict = json.loads(clean_text)
    except (json.JSONDecodeError, AttributeError):
        verdict = {"score": "error", "reasoning": "could not parse judge response"}

    return verdict