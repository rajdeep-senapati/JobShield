def collect_resume_evidence(resume_profile: dict) -> list[str]:
    evidence = []

    # Skills
    for category in resume_profile.get("skills", {}).values():
        evidence.extend(category)

    # Experience
    for experience in resume_profile.get("experience", []):
        evidence.append(experience.get("role", ""))
        evidence.append(experience.get("description", ""))

    # Projects
    for project in resume_profile.get("projects", []):
        evidence.append(project.get("name", ""))
        evidence.append(project.get("description", ""))
        evidence.extend(project.get("technologies", []))

    # Education
    for education in resume_profile.get("education", []):
        evidence.append(education.get("degree", ""))
        evidence.append(education.get("field", ""))

    return [item.strip() for item in evidence if item and item.strip()]


def collect_job_requirements(job_profile: dict) -> list[str]:
    requirements = []

    requirements.extend(job_profile.get("skills", []))

    requirements.extend(job_profile.get("responsibilities", []))

    requirements.extend(job_profile.get("qualifications", []))

    return [item.strip() for item in requirements if item and item.strip()]
