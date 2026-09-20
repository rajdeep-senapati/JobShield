import re

RISK_PATTERNS = {
    "upfront_payment": [
        r"pay.*fee",
        r"registration fee",
        r"processing fee",
        r"security deposit",
        r"pay.*deposit",
    ],
    "financial_information": [
        r"bank account",
        r"bank details",
        r"credit card",
        r"debit card",
        r"upi",
    ],
    "sensitive_personal_information": [
        r"aadhaar",
        r"pan card",
        r"passport",
        r"otp",
    ],
    "unrealistic_promises": [
        r"guaranteed.*job",
        r"guaranteed.*income",
        r"earn.*per day",
        r"earn.*per month",
        r"no experience.*high salary",
    ],
}

RISK_DESCRIPTIONS = {
    "upfront_payment": "The job appears to request an upfront payment or deposit.",
    "financial_information": "The job appears to request sensitive financial information.",
    "sensitive_personal_information": "The job appears to request sensitive personal information.",
    "unrealistic_promises": "The job contains potentially unrealistic income or employment promises.",
}

def detect_risk_signals(job) -> list:
    text = f"{job.title} {job.company} {job.description}".lower()

    signals = []

    for category, patterns in RISK_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                signals.append(category)
                break

    return signals


def assess_risk(job) -> dict:
    signals = detect_risk_signals(job)

    if len(signals) >= 3:
        risk_level = "high"
    elif len(signals) >= 1:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "risk_level": risk_level,
        "risk_signals": signals,
        "risk_explanations": [RISK_DESCRIPTIONS[signal] for signal in signals],
        "signal_count": len(signals),
    }
