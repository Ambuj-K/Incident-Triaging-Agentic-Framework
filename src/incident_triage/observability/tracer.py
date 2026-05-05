import os
from langfuse import Langfuse
from dotenv import load_dotenv

load_dotenv()

_langfuse = None

def get_langfuse() -> Langfuse:
    global _langfuse
    if _langfuse is None:
        _langfuse = Langfuse(
            public_key=os.environ["LANGFUSE_PUBLIC_KEY"],
            secret_key=os.environ["LANGFUSE_SECRET_KEY"],
            host=os.environ["LANGFUSE_HOST"],
        )
    return _langfuse


def create_trace(name: str, input_data: dict, metadata: dict = None):
    """Create a new Langfuse trace for an investigation."""
    lf = get_langfuse()
    return lf.trace(
        name=name,
        input=input_data,
        metadata=metadata or {},
    )
