from risk.analyzer import assess_risk
from ai.reasoner import generate_job_reasoning


def analyze_job(
    resume_text: str,
    job_text: str,
    client,
    risk_enabled: bool,
) -> dict:

    if risk_enabled:
        risk_result = assess_risk(
            job_text,
            client,
        )
    else:
        risk_result = {"risk_analysis_enabled": False}

    reasoning = generate_job_reasoning(
        resume_text,
        job_text,
        risk_result,
        client,
    )

    return {
        "risk": risk_result,
        "reasoning": reasoning,
    }
