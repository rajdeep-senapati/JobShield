from matching.evidence import (
    collect_job_requirements,
    collect_resume_evidence,
)

from matching.evidence_matcher import find_evidence_matches


def analyze_job_match(
    resume_profile: dict,
    job_profile: dict,
) -> dict:

    requirements = collect_job_requirements(job_profile)

    evidence = collect_resume_evidence(resume_profile)

    matches = find_evidence_matches(
        requirements,
        evidence,
    )

    exact_matches = [item for item in matches if item["match_type"] == "exact"]

    related_matches = [item for item in matches if item["match_type"] == "related"]

    missing_matches = [item for item in matches if item["match_type"] == "missing"]

    return {
        "requirements": requirements,
        "matches": matches,
        "summary": {
            "total_requirements": len(requirements),
            "exact_matches": len(exact_matches),
            "related_matches": len(related_matches),
            "missing_matches": len(missing_matches),
        },
    }
