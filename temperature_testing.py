import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY3"])

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="""Data pipeline from POS systems to data warehouse delayed by 6 hours. Yesterday's sales data not available for morning executive dashboard.""",
    config=types.GenerateContentConfig(
        system_instruction="""You are an incident triage assistant for a large retail company.
        For each incident, output JSON with exactly these fields:
        - severity: low/medium/high/critical
        (critical = complete outage or data loss, high = major degradation, 
        medium = partial impact, low = minor issue)
        - affected_systems: list of strings from known systems only
        - summary: under 20 words
        - immediate_actions: list of 2-3 strings
        - escalate: true or false
        - confidence: 0.0 to 1.0 as a float
        (1.0 = root cause confirmed, 0.5 = partial information, 
        0.1 = insufficient information)
        - If the incident describes potential impact not yet realized, 
        severity must not exceed high
        - Confidence must reflect information quality: 
        if root cause is unconfirmed, confidence must be below 0.7""",
        temperature=0,
        max_output_tokens=1000,
    )
)
for line in response.text.splitlines():
    print(line)