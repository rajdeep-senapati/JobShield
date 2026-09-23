from risk.analyzer import assess_risk
from ai.reasoner import generate_job_reasoning


def analyze_risk(
    job_text: str,
    client,
) -> dict:
    return assess_risk(
        job_text,
        client,
    )


def analyze_reasoning(
    resume_text: str,
    job_text: str,
    risk_result: dict,
    client,
) -> dict:
    return generate_job_reasoning(
        resume_text,
        job_text,
        risk_result,
        client,
    )
