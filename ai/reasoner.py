import json

from groq import Groq

MODEL = "openai/gpt-oss-120b"


def generate_job_reasoning(
    resume_profile: dict,
    job,
    match_result: dict,
    risk_result: dict,
    client: Groq,
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
- Explain why the candidate matches or does not match the job.
- Explain detected job-risk signals in plain language.
- If no risk signals are detected, say that no predefined risk indicators were found.
- Do not describe a low risk level as evidence that a job is unlikely to be a scam.
- State only which predefined risk indicators were or were not detected.
- Suggest resume improvements only when they directly address a missing job skill, requirement, or keyword.
- Do not invent tools, techniques, experience, or qualifications.
- Do not suggest adding a skill unless the resume already demonstrates evidence of it.
- Do not suggest generic resume improvements unrelated to this specific job.
- Do not claim that a job is definitely a scam or definitely legitimate.
- Do not make the final application decision for the user.
- "recommendation_context" should summarize factors the user can consider.
- Keep the response concise and useful.

JOBSHIELD DATA:
{json.dumps(context, indent=2)}
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
