from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

MODEL_NAME = "all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)


def calculate_similarity(requirement: str, evidence: str) -> float:
    embeddings = model.encode(
        [requirement, evidence],
        normalize_embeddings=True,
    )

    similarity = cosine_similarity(
        [embeddings[0]],
        [embeddings[1]],
    )[
        0
    ][0]

    return round(float(similarity), 4)


def find_semantic_matches(
    requirements: list[str],
    evidence: list[str],
    threshold: float = 0.45,
) -> list[dict]:

    results = []

    for requirement in requirements:
        best_match = None
        best_score = 0.0

        for item in evidence:
            score = calculate_similarity(
                requirement,
                item,
            )

            if score > best_score:
                best_score = score
                best_match = item

        results.append(
            {
                "requirement": requirement,
                "evidence": best_match,
                "similarity": best_score,
                "matched": best_score >= threshold,
            }
        )

    return results
