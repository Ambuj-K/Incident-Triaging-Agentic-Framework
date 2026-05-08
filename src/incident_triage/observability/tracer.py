import os
from langfuse import get_client
from dotenv import load_dotenv

load_dotenv()


def get_langfuse():
    """Get global Langfuse client configured from environment variables."""
    return get_client()
