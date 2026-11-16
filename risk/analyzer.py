import json

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from groq import Groq

MODEL = "openai/gpt-oss-20b"
RISK_THRESHOLD = 70


class RiskAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)

    risk_score: int = Field(ge=0, le=100)
    signals: list[str] = Field(default_factory=list)
    explanations: list[str] = Field(default_factory=list)


def assess_risk(
    job_text: str,
    client: Groq,
) -> dict:

    prompt = f"""
Analyze this job description for potential job-scam or safety risk signals.

Return ONLY valid JSON:

{{
    "risk_score": 0,
    "signals": [],
    "explanations": []
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

    content = response.choices[0].message.content

    if not content:
        raise ValueError("The risk analysis model returned an empty response.")

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"The risk analysis model returned invalid JSON: {exc}"
        ) from exc

    try:
        risk = RiskAnalysis.model_validate(parsed)
    except ValidationError as exc:
        raise ValueError(
            f"The risk analysis model returned an invalid response: {exc}"
        ) from exc

    result = risk.model_dump()

    score = result["risk_score"]

    if score >= RISK_THRESHOLD:
        result["risk_level"] = "high"
    elif score >= 30:
        result["risk_level"] = "medium"
    else:
        result["risk_level"] = "low"

    result["requires_confirmation"] = score >= RISK_THRESHOLD

    return result
