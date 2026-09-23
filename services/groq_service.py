import logging
from groq import Groq
from langfuse import observe
from config.settings import GROQ_API_KEY, GROQ_MODEL

# configure service logger
logger = logging.getLogger("groq_service")

# generate a linkedin post using the groq llm with langfuse tracing
@observe(name="generate_linkedin_post")
def generate_linkedin_post_content(topic: str = "modern software engineering and AI agents") -> str:
    # validate api key existence before initializing client
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set. Please provide it in the .env file.")

    # initialize groq sdk client
    client = Groq(api_key=GROQ_API_KEY)

    # define persona and formatting rules for post generation
    system_prompt = (
        "You are an expert LinkedIn content creator and tech thought leader. "
        "Write an engaging, insightful, and professional LinkedIn post on the requested topic. "
        "Include a strong hook, concise paragraphs or bullet points, a thought-provoking takeaway, "
        "and 3-5 relevant hashtags. Do not include markdown meta-text or commentary outside the post itself."
    )
    user_prompt = f"Create a compelling LinkedIn post about: {topic}"

    try:
        # request chat completion from groq api
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_completion_tokens=1024,
        )

        # extract generated message content
        post_text = completion.choices[0].message.content
        if not post_text:
            raise RuntimeError("received empty response from Groq LLM")

        return post_text.strip()

    except Exception as err:
        # log failure details and re-raise with original context
        logger.error(f"failed to generate post from Groq LLM: {err}")
        raise RuntimeError(f"Groq generation failed: {err}") from err
