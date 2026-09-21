from matching.matcher import analyze_job_match
from risk.analyzer import assess_risk
from ai.reasoner import generate_job_reasoning


def analyze_job(resume_profile: dict, job, job_profile: dict, client) -> dict:
    match_result = analyze_job_match(resume_profile, job_profile)
    risk_result = assess_risk(job)

    reasoning = generate_job_reasoning(
        resume_profile,
        job,
        match_result,
        risk_result,
        client,
    )

    return {
        "job": {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "source": job.source,
            "url": job.url,
        },
        "match": match_result,
        "risk": risk_result,
        "reasoning": reasoning,
    }
