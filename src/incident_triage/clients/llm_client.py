import instructor
from google import genai
from incident_triage.models.incident_report import IncidentReport
from incident_triage.config.llm_config import LLMConfig, DEFAULT_CONFIG
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

        Confidence definitions:
        - general_diagnosis_confidence: confidence based on common known failure patterns
        - system_specific_confidence: confidence given specific context provided.
        Set below 0.7 if root cause is unconfirmed.
        Set below 0.5 if no logs or diagnostic data provided.
        Set below 0.4 if no system context provided at all.
        Set below 0.3 if input is vague or ambiguous.

        Flags:
        - contradiction_detected: true if incident contains conflicting information
        - insufficient_context: true if input lacks enough detail for reliable triage
        - escalate: true if severity is high or critical, or if complexity is complex

        system_specific_confidence rules:
        - Must be below 0.5 if no logs or diagnostic data provided
        - Must be below 0.7 if root cause is unconfirmed
        - Must be below 0.4 if no system context provided at all
        - Must be below 0.3 if input is vague or ambiguous

        If potential impact is not yet realized, severity must not exceed high."""

    CONTEXT_SYSTEM_PROMPT = """You are an incident triage assistant for a large retail company.
        You have been provided with relevant runbooks and past incident reports to help
        investigate this incident. Use this institutional knowledge to produce a more
        accurate and specific investigation report.

        Base your analysis on the provided context where relevant. If the context
        contradicts the incident description, flag contradiction_detected as true.
        If the context is not relevant to this specific incident, rely on general
        knowledge and set system_specific_confidence appropriately.

        {context}

        ---

        Apply the same classification rules as always:

        Severity: critical=complete outage, high=major degradation, medium=partial impact, low=minor
        Complexity: simple=known pattern, medium=requires investigation, complex=novel/multi-system
        system_specific_confidence: raise above 0.5 only when retrieved context directly applies
        escalate: true if severity high or critical or complexity complex
        If potential impact not yet realized, severity must not exceed high."""

    def __init__(self, config: LLMConfig = DEFAULT_CONFIG):
        self.config = config
        raw_client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        self.client = instructor.from_genai(
            client=raw_client,
            mode=instructor.Mode.GENAI_STRUCTURED_OUTPUTS,
        )

    def triage_incident(self, incident_description: str) -> IncidentReport:
        """
        Pass 1 — Classify incident without context.
        Returns initial IncidentReport with affected_systems
        that can be used for retrieval.
        """
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

    def triage_with_context(
        self,
        incident_description: str,
        context: str,
    ) -> IncidentReport:
        """
        Pass 2 — Investigate incident with retrieved context.
        Produces grounded report with higher system_specific_confidence.
        """
        system_prompt = self.CONTEXT_SYSTEM_PROMPT.format(
            context=context
        )

        return self.client.chat.completions.create(
            model=self.config.model,
            response_model=IncidentReport,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": incident_description
                }
            ],
            max_retries=self.config.max_retries,
        )
