from pydantic import BaseModel, Field, field_validator
from typing import List
from enum import Enum

class Severity(str, Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'

class Complexity(str, Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"

class IncidentReport(BaseModel):
    severity: Severity = Field(
        description="critical=complete outage or data loss, high=major degradation, medium=partial impact, low=minor issue"
    )
    complexity: Complexity = Field(
        description="simple=known pattern with clear resolution, medium=requires investigation, complex=novel or multi-system with unclear cause"
    )
    affected_systems: List[str] = Field(
        description="List of affected systems. Only include systems explicitly mentioned or directly implied by the incident."
    )
    summary: str = Field(
        description="One sentence summary of the incident under 20 words"
    )
    immediate_actions: List[str] = Field(
        min_length=2,
        max_length=3,
        description="2 to 3 concrete immediate actions"
    )
    escalate: bool = Field(
        description="True if human escalation required"
    )
    general_diagnosis_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in general diagnosis based on common patterns"
    )
    system_specific_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence based on available system context. Low when retrieval returns nothing."
    )
    contradiction_detected: bool = Field(
        description="True if incident description contains conflicting information"
    )
    insufficient_context: bool = Field(
        description="True if input lacks enough information for reliable triage"
    )
    @field_validator("summary")
    @classmethod
    def summary_under_20_words(cls, v):
        word_count = len(v.split())
        if word_count > 20:
            raise ValueError(f"Summary is {word_count} words, must be under 20")
        return v

    @field_validator("affected_systems")
    @classmethod
    def no_empty_systems(cls, v):
        if not v:
            raise ValueError("affected_systems cannot be empty")
        return v
