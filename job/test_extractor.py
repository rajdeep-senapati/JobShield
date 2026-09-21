import json
import os

from dotenv import load_dotenv
from groq import Groq

from job.extractor import extract_job_profile

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


job_text = """
Data Analyst

ABC Technologies is looking for a Data Analyst in Bangalore.

Responsibilities:
- Analyze business data and generate insights.
- Build dashboards using Power BI.
- Write SQL queries.
- Use Python for data analysis.

Requirements:
- Strong SQL and Python skills.
- Experience with Power BI.
- Knowledge of data analysis and visualization.
- Full-time position.
"""


profile = extract_job_profile(job_text, client)


print(json.dumps(profile, indent=2))
