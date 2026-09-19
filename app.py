import os
import json

from dotenv import load_dotenv
from groq import Groq

from resume.parser import extract_resume_text
from resume.cleaner import clean_resume_text
from resume.extractor import extract_resume_profile

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

text = extract_resume_text("resume.pdf")
cleaned_text = clean_resume_text(text)

profile = extract_resume_profile(cleaned_text, client)

os.makedirs("data", exist_ok=True)

with open("data/resume_profile.json", "w", encoding="utf-8") as file:
    json.dump(profile, file, indent=2, ensure_ascii=False)

print("\nResume profile saved to data/resume_profile.json")
