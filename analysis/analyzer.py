from matching.matcher import analyze_job_match
from risk.analyzer import assess_risk


def analyze_job(resume_profile: dict, job) -> dict:
    match_result = analyze_job_match(resume_profile, job)
    risk_result = assess_risk(job)

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
    }
