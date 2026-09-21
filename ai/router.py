import os

from groq import Groq

PRIMARY_MODEL = "openai/gpt-oss-120b"
FALLBACK_MODEL = "openai/gpt-oss-20b"


def get_client() -> Groq:
    return Groq(api_key=os.getenv("GROQ_API_KEY"))


def get_reasoning_response(
    messages: list,
    client: Groq,
    stream: bool = False,
):
    try:
        response = client.chat.completions.create(
            model=PRIMARY_MODEL,
            messages=messages,
            temperature=0,
            stream=stream,
        )

        return {
            "response": response,
            "model": PRIMARY_MODEL,
            "fallback_used": False,
        }

    except Exception:
        response = client.chat.completions.create(
            model=FALLBACK_MODEL,
            messages=messages,
            temperature=0,
            stream=stream,
        )

        return {
            "response": response,
            "model": FALLBACK_MODEL,
            "fallback_used": True,
        }
