import re


def clean_resume_text(text: str) -> str:
    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)

    # Fix common PDF extraction artifacts
    replacements = {
        "F ull-Stack": "Full-Stack",
        "T echnologies": "Technologies",
        "T ools": "Tools",
        "T echnical": "Technical",
        "F eb": "Feb",
        "♂phone": "Phone: ",
        "✉": "Email: ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
