import json

from job.schema import Job


def load_job(job_data: dict) -> Job:
    return Job(
        title=job_data.get("title", ""),
        company=job_data.get("company", ""),
        location=job_data.get("location", ""),
        description=job_data.get("description", ""),
        skills=job_data.get("skills", []),
        employment_type=job_data.get("employment_type", ""),
        source=job_data.get("source", ""),
        url=job_data.get("url", ""),
    )


def load_job_from_json(file_path: str) -> Job:
    with open(file_path, "r", encoding="utf-8") as file:
        job_data = json.load(file)

    return load_job(job_data)
