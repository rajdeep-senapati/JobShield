import json
import streamlit as st

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
- Match only legitimate job qualifications: skills, experience, responsibilities, education, tools, and role-related requirements.
- Never treat payments, fees, deposits, Aadhaar, PAN, bank details, OTPs, identity documents, financial information, or other personal-data requests as job qualifications.
- Never include safety-related requests in strengths, gaps, match_score, or why_this_matches.
- Risk signals must be handled only by the risk analysis section and must not affect the match_score.
- Every strength must be directly supported by explicit resume evidence.
- Every strength must include concise resume evidence.
- Every gap must correspond to an explicit legitimate job requirement.
- Never create a gap from a safety-related request.
- Never treat missing resume information as a gap unless it is an explicit legitimate job requirement.
- Do not invent, infer, assume, or generalize skills, experience, responsibilities, achievements, metrics, qualifications, or soft skills.
- Do not infer experience from job titles, internships, projects, education, company names, or technology names.
- "Why this matches" must contain only direct connections between legitimate job requirements and explicit resume evidence.
- Resume improvements must focus on presenting or clarifying existing evidence.
- Do not recommend claiming skills that are not demonstrated in the resume.
- Keep strengths and gaps to a maximum of 4 each.
- Keep all points concise and non-repetitive.
- match_score must be an integer from 0 to 100.
- Calculate match_score only from legitimate job requirements supported by explicit resume evidence.
- If the job contains no legitimate requirements that can be matched against the resume, set match_score to 0, strengths to [], gaps to [], and why_this_matches to [].
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
    import streamlit as st

    st.write("### DEBUG — RAW 120B RESPONSE")
    st.code(content)

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
