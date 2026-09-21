def collect_resume_evidence(resume_profile: dict) -> list[dict]:
    evidence = []

    # Skills
    for category, skills in resume_profile.get("skills", {}).items():
        for skill in skills:
            if skill and skill.strip():
                evidence.append(
                    {
                        "text": skill.strip(),
                        "type": "skill",
                        "source": category,
                    }
                )

    # Experience
    for experience in resume_profile.get("experience", []):
        description = experience.get("description", "")

        if description and description.strip():
            evidence.append(
                {
                    "text": description.strip(),
                    "type": "experience",
                    "source": experience.get("company", ""),
                }
            )

    # Projects
    for project in resume_profile.get("projects", []):
        description = project.get("description", "")

        if description and description.strip():
            evidence.append(
                {
                    "text": description.strip(),
                    "type": "project",
                    "source": project.get("name", ""),
                }
            )

    # Education
    for education in resume_profile.get("education", []):
        education_text = " ".join(
            value
            for value in [
                education.get("degree", ""),
                education.get("field", ""),
            ]
            if value
        ).strip()

        if education_text:
            evidence.append(
                {
                    "text": education_text,
                    "type": "education",
                    "source": education.get("institution", ""),
                }
            )

    return evidence


def collect_job_requirements(job_profile: dict) -> list[dict]:
    requirements = []

    for skill in job_profile.get("skills", []):
        if skill and skill.strip():
            requirements.append(
                {
                    "text": skill.strip(),
                    "type": "skill",
                }
            )

    for responsibility in job_profile.get("responsibilities", []):
        if responsibility and responsibility.strip():
            requirements.append(
                {
                    "text": responsibility.strip(),
                    "type": "responsibility",
                }
            )

    for qualification in job_profile.get("qualifications", []):
        if qualification and qualification.strip():
            requirements.append(
                {
                    "text": qualification.strip(),
                    "type": "qualification",
                }
            )

    return requirements
