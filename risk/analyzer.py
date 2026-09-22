import json

from groq import Groq

MODEL = "openai/gpt-oss-20b"
RISK_THRESHOLD = 70


def assess_risk(
    job_text: str,
    client: Groq,
) -> dict:

    prompt = f"""
Analyze this job description for potential job-scam or safety risk signals.

Return ONLY valid JSON:

{{
    "risk_score": 0,
    "risk_level": "low",
    "signals": [],
    "explanations": [],
    "requires_confirmation": false
}}

Rules:
- Score from 0 to 100.
- This is a risk signal score, NOT scam probability.
- 0-29 = low.
- 30-69 = medium.
- 70-100 = high.
- Consider upfront payments, deposits, requests for financial information,
  sensitive identity information, OTPs, unrealistic income promises,
  guaranteed employment, and other suspicious recruitment patterns.
- Do not claim the job is definitely a scam.
- Keep explanations concise.
- requires_confirmation must be true when score >= 70.

JOB DESCRIPTION:
{job_text}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)
