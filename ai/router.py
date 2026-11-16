import logging

from groq import Groq

PRIMARY_MODEL = "openai/gpt-oss-120b"
FALLBACK_MODEL = "qwen/qwen3.8-27b"

logger = logging.getLogger(__name__)


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

    except Exception as primary_error:
        logger.warning(
            "Primary reasoning model failed (%s). Trying fallback model.",
            type(primary_error).__name__,
        )

        try:
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

        except Exception as fallback_error:
            raise RuntimeError(
                "Both reasoning models failed. "
                f"Primary error: {type(primary_error).__name__}; "
                f"fallback error: {type(fallback_error).__name__}."
            ) from fallback_error
