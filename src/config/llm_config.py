from dataclasses import dataclass

@dataclass
class LLMConfig:
    provider: str
    model: str
    temperature: float
    max_tokens: int
    max_retries: int

SIMPLE_CONFIG = LLMConfig(
    provider="gemini",
    model="gemini-2.5-flash",
    temperature=0,
    max_tokens=1000,
    max_retries=3,
)

COMPLEX_CONFIG = LLMConfig(
    provider="gemini",
    model="gemini-1.5-pro",
    temperature=0,
    max_tokens=1000,
    max_retries=3,
)

DEFAULT_CONFIG = SIMPLE_CONFIG