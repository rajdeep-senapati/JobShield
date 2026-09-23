import json

from ai.router import get_reasoning_response


def generate_job_reasoning(
    resume_text: str,
    job_text: str,
    risk_result: dict,
    client,
) -> dict:

    prompt = f"""
You are the main reasoning engine for JobShield.

Analyze the candidate's resume against the job description.

Return ONLY valid JSON with exactly this structure:

{{
    "match_score": 0,
    "match_summary": "",
    "strengths": [
        {{
            "point": "",
            "evidence": ""
        }}
    ],
    "gaps": [
        {{
            "point": "",
            "job_requirement": ""
        }}
    ],
    "why_this_matches": [],
    "resume_improvements": [],
    "things_to_consider": []
}}

Rules:
- Use only information explicitly present in the resume and job description.
- Do not invent, infer, assume, or generalize skills, experience, responsibilities, achievements, metrics, tools, qualifications, or soft skills.
- Do not infer experience from job titles, internships, projects, education, company names, or technology names.
- Do not assume that experience with one technology means experience with a related technology.
- Do not infer proficiency merely because a technology appears in the skills section.
- Every strength must be directly supported by explicit resume evidence.
- Every strength must include concise evidence that quotes or closely reproduces the resume.
- Every gap must correspond to an explicit requirement in the job description.
- Every gap must include the relevant job requirement.
- Do not treat missing information in the resume as a gap unless the job description explicitly requires it.
- If explicit evidence is unavailable, do not make an assumption.
- "Why this matches" must contain only direct connections between explicit resume evidence and explicit job requirements.
- Resume improvements must focus on presenting, clarifying, or quantifying existing evidence.
- Do not recommend claiming or adding a skill that the resume does not demonstrate.
- Keep strengths and gaps to a maximum of 4 each.
- Keep all points concise, specific, and non-repetitive.
- Prioritize the most relevant job requirements.
- match_score must be an integer from 0 to 100.
- Calculate match_score only from explicit matches between resume evidence and explicit job requirements.
- Do not award points for inferred, transferable, assumed, or general employability factors.
- Do not infer communication, leadership, teamwork, independence, or remote-work ability.
- Do not make the final application decision for the user.

RISK ANALYSIS:
{json.dumps(risk_result, indent=2)}

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_text}
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

    content = result["response"].choices[0].message.content.strip()

    decoder = json.JSONDecoder()

    start = content.find("{")

    if start == -1:
        raise ValueError("Model did not return JSON.")

    try:
        reasoning, _ = decoder.raw_decode(content[start:])
    except json.JSONDecodeError as e:
        raise ValueError(f"Model returned invalid JSON: {e}")

    reasoning["_model"] = result["model"]
    reasoning["_fallback_used"] = result["fallback_used"]

    return reasoning
