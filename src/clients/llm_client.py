import instructor
from google import genai
from models.incident_report import IncidentReport
from config.llm_config import LLMConfig, DEFAULT_CONFIG
import os


class LLMClient:

    SYSTEM_PROMPT = """You are an incident triage assistant for a large retail company.
        For each incident, classify and structure your response carefully.

        Complexity definitions:
        - simple: single system affected, known error type, clear fix exists,
        affects one user or non-critical system, runbook likely exists
        - medium: multiple systems potentially affected, root cause unclear
        but contained, requires investigation, moderate business impact
        - complex: multi-system cascade, novel failure pattern, no clear
        resolution path, high business impact, requires senior engineering

        Severity definitions:
        - critical: complete outage or data loss, impact happening now, all users affected
        - high: major degradation or potential impact not yet realized, significant business impact
        - medium: partial impact, subset of users or systems affected, workaround exists
        - low: minor issue, minimal business impact, no urgency

        Complexity definitions:
        - simple: known pattern with clear resolution path, runbook exists
        - medium: requires investigation, root cause unclear but contained
        - complex: novel situation, multi-system failure, unclear cause, no clear runbook

        Confidence definitions:
        - general_diagnosis_confidence: confidence based on common known failure patterns
        - system_specific_confidence: confidence given specific context provided.
        Set below 0.7 if root cause is unconfirmed.
        Set below 0.4 if no system-specific context is provided.
        Set below 0.3 if input is vague or ambiguous.

        Flags:
        - contradiction_detected: true if incident contains conflicting information
        - insufficient_context: true if input lacks enough detail for reliable triage
        - escalate: true if severity is high or critical, or if complexity is complex

        If potential impact is not yet realized, severity must not exceed high."""

    def __init__(self, config: LLMConfig = DEFAULT_CONFIG):
        self.config = config
        raw_client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        self.client = instructor.from_genai(
            client=raw_client,
            mode=instructor.Mode.GENAI_STRUCTURED_OUTPUTS,
        )

    def triage_incident(self, incident_description: str) -> IncidentReport:
        return self.client.chat.completions.create(
            model=self.config.model,
            response_model=IncidentReport,
            messages=[
                {
                    "role": "system",
                    "content": self.SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": incident_description
                }
            ],
            max_retries=self.config.max_retries,
        )