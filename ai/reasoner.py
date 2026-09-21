import json

from ai.router import get_reasoning_response


def generate_job_reasoning(
    resume_profile: dict,
    job,
    match_result: dict,
    risk_result: dict,
    client,
) -> dict:

    context = {
        "resume_profile": resume_profile,
        "job": {
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "description": job.description,
            "skills": job.skills,
        },
        "match_result": match_result,
        "risk_result": risk_result,
    }

    prompt = f"""
You are the reasoning engine for JobShield.

Analyze the provided resume, job, deterministic match results,
and deterministic risk signals.

Return ONLY valid JSON using exactly this structure:

{{
    "summary": "",
    "why_it_matches": [],
    "missing_skills": [],
    "risk_explanation": "",
    "resume_improvements": [],
    "recommendation_context": ""
}}

Rules:
- Do not invent information.
- Use the deterministic match and risk results as evidence.
- Do not override or contradict those results.
- Explain the candidate-job alignment using evidence from the resume.
- Explain detected job-risk signals in plain language.
- If no risk signals are detected, say that no predefined risk indicators were found.
- Do not describe a low risk level as evidence that a job is unlikely to be a scam.
- Suggest resume improvements only when directly supported by the resume and job.
- Do not invent skills, experience, or qualifications.
- Do not claim that a job is definitely a scam or definitely legitimate.
- Do not make the final application decision for the user.
- "recommendation_context" should summarize factors the user can consider.
- Keep the response concise and useful.

JOBSHIELD DATA:
{json.dumps(context, indent=2)}
"""

    result = get_reasoning_response(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        client=client,
        stream=False,
    )

    content = result["response"].choices[0].message.content

    reasoning = json.loads(content)

    reasoning["_model"] = result["model"]
    reasoning["_fallback_used"] = result["fallback_used"]

    return reasoning
