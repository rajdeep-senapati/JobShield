from matching.semantic_matcher import calculate_similarity


def normalize_text(text: str) -> str:
    return text.strip().lower()

def get_allowed_evidence_types(requirement_type: str) -> set[str]:
    if requirement_type == "skill":
        return {
            "skill",
            "experience",
            "project",
        }

    if requirement_type == "responsibility":
        return {
            "experience",
            "project",
        }

    if requirement_type == "qualification":
        return {
            "education",
            "experience",
            "project",
            "skill",
        }

    return {
        "skill",
        "experience",
        "project",
        "education",
    }


def find_evidence_matches(
    requirements: list[dict],
    evidence: list[dict],
    semantic_threshold: float = 0.45,
) -> list[dict]:

    results = []

    normalized_evidence = {normalize_text(item["text"]): item for item in evidence}

    for requirement in requirements:

        requirement_text = requirement["text"]
        requirement_type = requirement["type"]

        normalized_requirement = normalize_text(requirement_text)

        allowed_types = get_allowed_evidence_types(requirement_type)

        # Exact match
        exact_evidence = normalized_evidence.get(normalized_requirement)

        if exact_evidence and exact_evidence["type"] in allowed_types:
            results.append(
                {
                    "requirement": requirement_text,
                    "type": requirement_type,
                    "evidence": exact_evidence["text"],
                    "evidence_type": exact_evidence["type"],
                    "evidence_source": exact_evidence["source"],
                    "similarity": 1.0,
                    "match_type": "exact",
                }
            )
            continue

        # Semantic matching only against appropriate evidence
        best_evidence = None
        best_score = 0.0

        for item in evidence:

            if item["type"] not in allowed_types:
                continue

            score = calculate_similarity(
                requirement_text,
                item["text"],
            )

            if score > best_score:
                best_score = score
                best_evidence = item

        if best_score >= semantic_threshold:
            match_type = "related"
        else:
            match_type = "missing"

        results.append(
            {
                "requirement": requirement_text,
                "type": requirement_type,
                "evidence": (best_evidence["text"] if best_evidence else None),
                "evidence_type": (best_evidence["type"] if best_evidence else None),
                "evidence_source": (best_evidence["source"] if best_evidence else None),
                "similarity": round(best_score, 4),
                "match_type": match_type,
            }
        )

    return results
