import json

from groq import Groq

MODEL = "openai/gpt-oss-20b"


def extract_resume_profile(resume_text: str, client: Groq) -> dict:
    prompt = f"""
You are the resume extraction engine for JobShield.

Extract information from the resume and return ONLY valid JSON.

The JSON MUST follow this exact schema:

{{
    "name": "",
    "education": [
        {{
            "institution": "",
            "degree": "",
            "field": "",
            "start": "",
            "end": ""
        }}
    ],
    "experience": [
        {{
            "company": "",
            "role": "",
            "location": "",
            "start": "",
            "end": "",
            "description": ""
        }}
    ],
    "projects": [
        {{
            "name": "",
            "technologies": [],
            "description": ""
        }}
    ],
    "skills": {{
        "programming": [],
        "data_science_ml": [],
        "cloud": [],
        "databases": [],
        "frameworks_tools": []
    }},
    "target_roles": []
}}

STRICT RULES:
- Follow the schema exactly.
- Never change field names.
- Never change an object into a string.
- Use empty strings when information is unavailable.
- Use empty arrays when no information is available.
- Only extract information supported by the resume.
- Do not invent qualifications or experience.
- Keep descriptions concise.
- Preserve important technologies.
- Do not infer target roles from individual technologies alone.

RESUME:
{resume_text}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content

    return json.loads(content)
