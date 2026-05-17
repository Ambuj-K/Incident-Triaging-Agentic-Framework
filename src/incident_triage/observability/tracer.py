import os
from langfuse import get_client
from dotenv import load_dotenv

load_dotenv()


def get_langfuse():
    return get_client()


def flush():
    lf = get_langfuse()
    lf.flush()


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "gemini-3.1-flash-lite",
) -> float:
    """
    Estimate cost in USD for a single LLM call.
    Prices per million tokens as of May 2026.
    """
    pricing = {
        "gemini-3.1-flash-lite": {
            "input": 0.10 / 1_000_000,
            "output": 0.40 / 1_000_000,
        },
        "gemini-2.5-flash": {
            "input": 0.15 / 1_000_000,
            "output": 0.60 / 1_000_000,
        },
        "gemini-3.1-flash": {
            "input": 0.30 / 1_000_000,
            "output": 1.20 / 1_000_000,
        },
    }

    if model not in pricing:
        return 0.0

    return (
        input_tokens * pricing[model]["input"] +
        output_tokens * pricing[model]["output"]
    )
