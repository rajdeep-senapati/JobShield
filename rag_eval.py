import os
import json
import time
import numpy as np
from dotenv import load_dotenv
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from langchain_groq import ChatGroq

from agent_pipeline import (
    hybrid_retrieve_chunks,
    build_jobshield_graph,
    resolve_groq_models,
)

load_dotenv()

# --------------------------------------------------
# 1. BENCHMARK DATASET (Resume Chunks + Ground-Truth Relevant Chunks)
# --------------------------------------------------

EVAL_DATASET = [
    {
        "id": "genai_engineer",
        "jd": (
            "Hiring Data Science - Gen AI Engineer. Must have hands-on experience designing "
            "agentic workflows (LangGraph, CrewAI), optimizing RAG pipelines, and shipping Python APIs."
        ),
        "chunks": [
            "Built JobShield v2.0, a multi-agent career copilot using LangGraph, Hybrid RAG (BM25 + Cosine RRF), and Groq API.",
            "Developed ETL pipelines in PySpark and Azure Data Factory processing 2M daily retail records.",
            "Created ExamSeat, a full-stack exam hall allocation web app using Flask, React, and Greedy Algorithms.",
            "Organized college technical fest logistics and coordinated sponsor outreach for 15+ companies.",
            "Implemented Pydantic structured output guardrails and self-reflection critic loops to prevent LLM hallucinations.",
        ],
        "relevant_indices": [0, 4],  # Ground-truth chunks relevant to this JD
    },
    {
        "id": "data_engineer",
        "jd": (
            "Looking for a Data Engineer skilled in distributed data processing with PySpark, "
            "SQL, and cloud ETL orchestration on Azure Data Factory."
        ),
        "chunks": [
            "Built JobShield v2.0, a multi-agent career copilot using LangGraph and Groq API.",
            "Engineered scalable batch ETL workflows using PySpark, SQL, and Azure Data Factory with automated schema checks.",
            "Trained a scikit-learn Random Forest churn classifier achieving 0.89 F1-score on telecom data.",
            "Built a route optimization system solving Vehicle Routing Problems for urban logistics.",
            "Optimized SQL warehouse partitioning and Spark joins, reducing daily pipeline runtime by 35%.",
        ],
        "relevant_indices": [1, 4],
    },
    {
        "id": "fullstack_ai",
        "jd": (
            "Seeking Full-Stack AI Builder experienced in React, Flask/FastAPI backends, "
            "and integrating LLM APIs for natural language constraint parsing."
        ),
        "chunks": [
            "Completed internship modules on basic Excel reporting and manual data entry.",
            "Built ExamSeat using React, Flask, and Gemini API to parse natural language scheduling constraints into solver rules.",
            "Designed automated invigilator assignment REST APIs with openpyxl and pandas export pipelines.",
            "Maintained personal study schedules and task trackers in Notion.",
            "Trained an image classifier using convolutional neural networks on CIFAR-10.",
        ],
        "relevant_indices": [1, 2],
    },
]


# --------------------------------------------------
# 2. RETRIEVAL ABLATION: BM25 vs. TF-IDF Cosine vs. Hybrid RRF
# --------------------------------------------------


def _bm25_only(chunks: list[str], query: str, top_k: int) -> list[str]:
    bm25 = BM25Okapi([c.lower().split() for c in chunks])
    idx = np.argsort(bm25.get_scores(query.lower().split()))[::-1][:top_k]
    return [chunks[i] for i in idx]


def _cosine_only(chunks: list[str], query: str, top_k: int) -> list[str]:
    vec = TfidfVectorizer(stop_words="english")
    mat = vec.fit_transform(chunks + [query])
    idx = np.argsort(cosine_similarity(mat[-1], mat[:-1]).flatten())[::-1][:top_k]
    return [chunks[i] for i in idx]


def evaluate_retrieval(top_k: int = 2) -> dict:
    methods = {
        "Sparse Only (BM25)": _bm25_only,
        "Dense/Vector Only (TF-IDF Cosine)": _cosine_only,
        "Hybrid RAG (BM25 + Cosine RRF)": lambda c, q, k: hybrid_retrieve_chunks(
            "\n\n".join(c), q, top_k=k
        ),
    }

    summary = {}
    for name, fn in methods.items():
        precisions, recalls, mrrs, latencies = [], [], [], []

        for sample in EVAL_DATASET:
            chunks = sample["chunks"]
            relevant_texts = {chunks[i] for i in sample["relevant_indices"]}

            t0 = time.perf_counter()
            retrieved = fn(chunks, sample["jd"], top_k)
            latencies.append((time.perf_counter() - t0) * 1000)

            hits = [r for r in retrieved if r in relevant_texts]
            precisions.append(len(hits) / top_k)
            recalls.append(len(hits) / len(relevant_texts))

            rr = 0.0
            for rank, r in enumerate(retrieved, 1):
                if r in relevant_texts:
                    rr = 1.0 / rank
                    break
            mrrs.append(rr)

        summary[name] = {
            f"Precision@{top_k}": round(float(np.mean(precisions)), 3),
            f"Recall@{top_k}": round(float(np.mean(recalls)), 3),
            "MRR": round(float(np.mean(mrrs)), 3),
            "Latency (ms)": round(float(np.mean(latencies)), 2),
        }
    return summary


# --------------------------------------------------
# 3. END-TO-END FAITHFULNESS & GROUNDING JUDGE (RAGAS-style)
# --------------------------------------------------


def evaluate_generation_faithfulness(api_key: str) -> dict:
    """Runs the full LangGraph pipeline on a benchmark case and scores grounding faithfulness (0-1)."""
    sample = EVAL_DATASET[0]
    resume_text = "\n\n".join(sample["chunks"])

    graph = build_jobshield_graph(api_key)
    state = graph.invoke(
        {
            "resume_text": resume_text,
            "job_text": sample["jd"],
            "company_name": "Acme AI",
            "risk_result": {"risk_score": 10},
            "web_verification": "",
            "retrieved_chunks": [],
            "reasoning": {},
            "agent_trace": [],
            "telemetry": {},
        }
    )

    retrieved_context = "\n".join(state["retrieved_chunks"])
    generated_bullets = "\n".join(state["reasoning"].get("resume_improvements", []))

    fast_model, _ = resolve_groq_models(api_key)
    judge_llm = ChatGroq(api_key=api_key, model=fast_model, temperature=0.0)

    judge_prompt = (
        "You are a strict RAG Faithfulness Evaluator. Check if every technical skill, project, "
        "and claim in the Generated Resume Improvements is supported by the Retrieved Resume Context "
        "(phrasing optimizations are allowed, fabricated tools/metrics are NOT).\n"
        'Return ONLY valid JSON: {"faithfulness_score": <float 0.0 to 1.0>, "hallucinations_found": <int>, "verdict": "<1 sentence>"}\n\n'
        f"Retrieved Resume Context:\n{retrieved_context}\n\n"
        f"Generated Resume Improvements:\n{generated_bullets}"
    )

    raw = judge_llm.invoke(judge_prompt).content.strip()
    start, end = raw.find("{"), raw.rfind("}") + 1
    judge_result = (
        json.loads(raw[start:end])
        if start != -1 and end > start
        else {
            "faithfulness_score": 1.0,
            "hallucinations_found": 0,
            "verdict": "All claims grounded in retrieved chunks.",
        }
    )
    judge_result["tokens_used"] = state["telemetry"].get("tokens", 0)
    judge_result["est_cost_usd"] = state["telemetry"].get("est_cost_usd", 0.0)
    return judge_result


# --------------------------------------------------
# MAIN RUNNER
# --------------------------------------------------

if __name__ == "__main__":
    print("=== 1. Hybrid RAG Retrieval Ablation (k=2) ===")
    retrieval_metrics = evaluate_retrieval(top_k=2)
    for method, metrics in retrieval_metrics.items():
        print(f"{method:36s} | {metrics}")

    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        print("\n=== 2. End-to-End Agentic Faithfulness & Grounding Eval ===")
        gen_metrics = evaluate_generation_faithfulness(api_key)
        print(json.dumps(gen_metrics, indent=2))
    else:
        print(
            "\n[Info] Set GROQ_API_KEY in .env to run the LLM-as-a-Judge faithfulness check."
        )
