from matching.semantic_matcher import calculate_similarity


def normalize_text(text: str) -> str:
    return text.strip().lower()


def find_evidence_matches(
    requirements: list[str],
    evidence: list[str],
    semantic_threshold: float = 0.40,
) -> list[dict]:

    results = []

    normalized_evidence = {normalize_text(item): item for item in evidence}

    for requirement in requirements:

        normalized_requirement = normalize_text(requirement)

        # Exact match
        if normalized_requirement in normalized_evidence:
            results.append(
                {
                    "requirement": requirement,
                    "evidence": normalized_evidence[normalized_requirement],
                    "similarity": 1.0,
                    "match_type": "exact",
                }
            )
            continue

        # Semantic / related match
        best_evidence = None
        best_score = 0.0

        for item in evidence:
            score = calculate_similarity(
                requirement,
                item,
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
                "requirement": requirement,
                "evidence": best_evidence,
                "similarity": best_score,
                "match_type": match_type,
            }
        )

    return results
