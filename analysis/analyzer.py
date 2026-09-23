import re

from risk.analyzer import assess_risk
from ai.reasoner import generate_job_reasoning

SAFETY_TERMS = [
    "registration fee",
    "security deposit",
    "upfront payment",
    "payment",
    "deposit",
    "aadhaar",
    "aadhar",
    "pan card",
    "bank account",
    "bank details",
    "otp",
    "one-time password",
    "personal identification",
    "identity document",
    "financial information",
]


def _is_safety_related(text: str) -> bool:
    text = text.lower()
    return any(term in text for term in SAFETY_TERMS)


def _filter_reasoning(reasoning: dict) -> dict:

    reasoning["why_this_matches"] = [
        item
        for item in reasoning.get("why_this_matches", [])
        if not _is_safety_related(str(item))
    ]

    reasoning["resume_improvements"] = [
        item
        for item in reasoning.get("resume_improvements", [])
        if not _is_safety_related(str(item))
    ]

    reasoning["things_to_consider"] = [
        item
        for item in reasoning.get("things_to_consider", [])
        if not _is_safety_related(str(item))
    ]

    return reasoning


def analyze_risk(
    job_text: str,
    client,
) -> dict:
    return assess_risk(
        job_text,
        client,
    )


def analyze_reasoning(
    resume_text: str,
    job_text: str,
    risk_result: dict,
    client,
) -> dict:

    reasoning = generate_job_reasoning(
        resume_text,
        job_text,
        risk_result,
        client,
    )

    return _filter_reasoning(reasoning)
