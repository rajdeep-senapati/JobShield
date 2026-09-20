import json
import os

from dotenv import load_dotenv
from groq import Groq

from analysis.analyzer import analyze_job
from job.loader import load_job_from_json
from resume.profile import load_resume_profile, load_user_preferences
from ai.reasoner import generate_job_reasoning

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

job = load_job_from_json("data/sample_job.json")

resume_profile = load_resume_profile("data/resume_profile.json")

preferences = load_user_preferences("data/user_preferences.json")

resume_profile["target_roles"] = preferences.get("target_roles", [])

analysis = analyze_job(resume_profile, job)

reasoning = generate_job_reasoning(
    resume_profile,
    job,
    analysis["match"],
    analysis["risk"],
    client,
)

print("\n--- GPT-OSS REASONING ---\n")
print(json.dumps(reasoning, indent=2))
