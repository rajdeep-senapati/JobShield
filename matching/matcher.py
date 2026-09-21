def normalize_skill(skill: str) -> str:
    skill = skill.strip().lower()

    aliases = {
        "powerbi": "power bi",
        "scikit learn": "scikit-learn",
        "sklearn": "scikit-learn",
        "py torch": "pytorch",
    }

    return aliases.get(skill, skill)


def get_resume_skills(resume_profile: dict) -> set:
    skills = set()

    for category in resume_profile.get("skills", {}).values():
        for skill in category:
            skills.add(normalize_skill(skill))

    return skills


def get_resume_evidence(resume_profile: dict) -> set:
    evidence = set()

    for skill in get_resume_skills(resume_profile):
        evidence.add(skill)

    for experience in resume_profile.get("experience", []):
        evidence.add(normalize_skill(experience.get("role", "")))
        evidence.add(normalize_skill(experience.get("description", "")))

    for project in resume_profile.get("projects", []):
        evidence.add(normalize_skill(project.get("name", "")))
        evidence.add(normalize_skill(project.get("description", "")))

        for technology in project.get("technologies", []):
            evidence.add(normalize_skill(technology))

    return {item for item in evidence if item}


def match_skills(resume_profile: dict, job) -> dict:
    resume_skills = get_resume_skills(resume_profile)

    job_skills = {normalize_skill(skill) for skill in job.skills}

    matched = resume_skills & job_skills
    missing = job_skills - resume_skills

    match_percentage = len(matched) / len(job_skills) * 100 if job_skills else 0

    return {
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing),
        "skill_match_percentage": round(match_percentage, 2),
    }


def match_job_title(resume_profile: dict, job) -> dict:
    target_roles = {
        normalize_skill(role) for role in resume_profile.get("target_roles", [])
    }

    job_title = normalize_skill(job.title)

    matched_roles = [
        role for role in target_roles if role in job_title or job_title in role
    ]

    return {
        "matched_roles": sorted(matched_roles),
        "title_match": bool(matched_roles),
    }


def analyze_job_match(resume_profile: dict, job) -> dict:
    skill_result = match_skills(resume_profile, job)

    title_result = match_job_title(resume_profile, job)

    skill_score = skill_result["skill_match_percentage"]
    title_score = 100 if title_result["title_match"] else 0

    final_score = skill_score * 0.70 + title_score * 0.30

    return {
        "job_title": job.title,
        "company": job.company,
        "match_score": round(final_score, 2),
        "skill_match": skill_result,
        "title_match": title_result,
    }
