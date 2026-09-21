import json

from groq import Groq

MODEL = "openai/gpt-oss-20b"
stream = False

def extract_job_profile(job_text: str, client: Groq) -> dict:

    prompt = f"""
You are the job extraction engine for JobShield.

Extract structured information from the provided job description.

Return ONLY valid JSON using exactly this schema:

{{
    "title": "",
    "company": "",
    "location": "",
    "employment_type": "",
    "skills": [],
    "responsibilities": [],
    "qualifications": [],
    "description": ""
}}

STRICT RULES:

- Follow the schema exactly.
- Never change field names.
- Use empty strings when information is unavailable.
- Use an empty array when no skills are found.
- Only extract information explicitly supported by the job description.
- Do not invent company names, skills, locations, or requirements.
- Extract technical and relevant job skills such as Python, SQL, AWS,
  Power BI, Machine Learning, Excel, etc.
- Keep the description concise while preserving the main responsibilities
  and requirements.
- Do not infer skills from the job title alone.

JOB DESCRIPTION:

{job_text}
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
