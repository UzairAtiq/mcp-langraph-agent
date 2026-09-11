from langchain_groq import ChatGroq
from config.settings import GROQ_API_KEY
import json

# separate llm just for judging, no tools needed here
judge_llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=GROQ_API_KEY
)


async def judge_response(result):

    # build the prompt for the judge using values from the result dict
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

    # ask the judge llm
    response = await judge_llm.ainvoke(judge_prompt)

    # try to parse the json reply
    try:
        clean_text = response.content.replace("```json", "").replace("```", "").strip()
        verdict = json.loads(clean_text)
    except json.JSONDecodeError:
        verdict = {"score": "error", "reasoning": "could not parse judge response"}

    return verdict