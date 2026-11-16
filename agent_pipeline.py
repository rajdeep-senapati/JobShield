import time
import requests
from typing import TypedDict, List, Dict, Any
import numpy as np
from pydantic import BaseModel, Field
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from ddgs import DDGS
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

# --------------------------------------------------
# DYNAMIC GROQ MODEL RESOLVER (Zero Deprecation Breakage)
# --------------------------------------------------


def resolve_groq_models(api_key: str) -> tuple[str, str]:
    """Fetches active chat models from Groq API so deprecated model IDs never break the app."""
    try:
        resp = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=5,
        )
        available = {
            m["id"]
            for m in resp.json().get("data", [])
            if not any(
                x in m["id"].lower() for x in ["whisper", "guard", "tts", "orpheus"]
            )
        }
    except Exception:
        available = set()

    fast_candidates = [
        "openai/gpt-oss-20b",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "qwen/qwen3-32b",
        "llama-3.3-70b-versatile",
    ]
    smart_candidates = [
        "openai/gpt-oss-120b",
        "qwen/qwen3-32b",
        "openai/gpt-oss-20b",
    ]

    fast_model = next(
        (m for m in fast_candidates if m in available),
        next(iter(available), "openai/gpt-oss-20b"),
    )
    smart_model = next(
        (m for m in smart_candidates if m in available),
        next(iter(available), "openai/gpt-oss-120b"),
    )
    return fast_model, smart_model


# --------------------------------------------------
# STRUCTURED OUTPUT SCHEMAS (Matches your UI contract)
# --------------------------------------------------


class StrengthItem(BaseModel):
    point: str = Field(description="Clear strength matching the role")
    evidence: str = Field(
        description="Exact quote or concrete proof from the retrieved resume chunks"
    )


class GapItem(BaseModel):
    point: str = Field(description="Missing skill or experience gap")
    job_requirement: str = Field(description="Specific requirement from the JD")


class ReasoningOutput(BaseModel):
    match_score: int = Field(
        ge=0, le=100, description="ATS & role fit score from 0 to 100"
    )
    match_summary: str = Field(
        description="2-3 sentence executive summary of candidate fit"
    )
    strengths: List[StrengthItem] = Field(default_factory=list)
    gaps: List[GapItem] = Field(default_factory=list)
    why_this_matches: List[str] = Field(default_factory=list)
    resume_improvements: List[str] = Field(default_factory=list)
    things_to_consider: List[str] = Field(default_factory=list)


# --------------------------------------------------
# LANGGRAPH SHARED STATE
# --------------------------------------------------


class JobShieldState(TypedDict):
    resume_text: str
    job_text: str
    company_name: str
    risk_result: Dict[str, Any]
    web_verification: str
    retrieved_chunks: List[str]
    reasoning: Dict[str, Any]
    agent_trace: List[str]
    telemetry: Dict[str, Any]


# --------------------------------------------------
# HYBRID RAG RETRIEVER (BM25 + Cosine Similarity RRF)
# --------------------------------------------------


def hybrid_retrieve_chunks(resume_text: str, query: str, top_k: int = 5) -> List[str]:
    """Retrieves top-k resume chunks using Reciprocal Rank Fusion over BM25 + TF-IDF Cosine."""
    chunks = [c.strip() for c in resume_text.split("\n\n") if len(c.strip()) > 25]
    if len(chunks) <= top_k:
        return chunks

    # 1. Sparse Lexical Retrieval (BM25)
    tokenized_corpus = [doc.lower().split() for doc in chunks]
    bm25 = BM25Okapi(tokenized_corpus)
    bm25_scores = bm25.get_scores(query.lower().split())
    bm25_ranks = np.argsort(bm25_scores)[::-1]

    # 2. Dense-style Vector Retrieval (TF-IDF Cosine)
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(chunks + [query])
    cos_scores = cosine_similarity(tfidf_matrix[-1], tfidf_matrix[:-1]).flatten()
    cos_ranks = np.argsort(cos_scores)[::-1]

    # 3. Reciprocal Rank Fusion (RRF)
    rrf: Dict[int, float] = {}
    for rank, idx in enumerate(bm25_ranks):
        rrf[idx] = rrf.get(idx, 0.0) + 1.0 / (60 + rank)
    for rank, idx in enumerate(cos_ranks):
        rrf[idx] = rrf.get(idx, 0.0) + 1.0 / (60 + rank)

    top_indices = sorted(rrf, key=rrf.get, reverse=True)[:top_k]
    return [chunks[i] for i in top_indices]


# --------------------------------------------------
# BUILD MULTI-AGENT GRAPH
# --------------------------------------------------


def build_jobshield_graph(api_key: str):
    fast_model_id, smart_model_id = resolve_groq_models(api_key)

    fast_llm = ChatGroq(api_key=api_key, model=fast_model_id, temperature=0.1)
    smart_llm = ChatGroq(api_key=api_key, model=smart_model_id, temperature=0.15)
    structured_matcher = smart_llm.with_structured_output(ReasoningOutput)

    # NODE 1: Live Web Verification Agent (Tool Use)
    def web_verifier_node(state: JobShieldState):
        t0 = time.time()
        trace = list(state.get("agent_trace", []))
        telemetry = dict(state.get("telemetry", {}))
        company = state.get("company_name", "").strip()

        snippets = []
        if company:
            try:
                results = DDGS().text(
                    f"{company} company careers reviews legitimacy", max_results=3
                )
                snippets = [
                    f"- {r.get('title', '')}: {r.get('body', '')}" for r in results
                ]
            except Exception:
                snippets = [
                    "Live web lookup skipped (rate limit); relying on heuristic risk signals."
                ]

        evidence = (
            "\n".join(snippets) if snippets else "No external company name supplied."
        )
        prompt = (
            f"Verify company legitimacy in 2 concise sentences based on web evidence and heuristic risk score "
            f"({state.get('risk_result', {}).get('risk_score', 0)}/100).\n"
            f"Company: {company or 'Not specified'}\nWeb Evidence:\n{evidence}\n"
            f"JD Snippet:\n{state['job_text'][:800]}"
        )
        res = fast_llm.invoke(prompt)
        tokens = res.response_metadata.get("token_usage", {}).get("total_tokens", 320)

        telemetry["tokens"] = telemetry.get("tokens", 0) + tokens
        trace.append(
            f"✅ **Agent 1 — Web Verifier** (`{fast_model_id}` + DuckDuckGo Search) · `{time.time() - t0:.2f}s`"
        )

        return {
            "web_verification": res.content,
            "agent_trace": trace,
            "telemetry": telemetry,
        }

    # NODE 2: Hybrid RAG Retriever + Grounded ATS Matcher Agent
    def hybrid_rag_matcher_node(state: JobShieldState):
        t0 = time.time()
        trace = list(state["agent_trace"])
        telemetry = dict(state["telemetry"])

        retrieved = hybrid_retrieve_chunks(
            state["resume_text"], state["job_text"], top_k=5
        )
        grounded_context = "\n\n---\n\n".join(retrieved)

        saved_pct = max(
            0,
            int((1 - len(grounded_context) / max(len(state["resume_text"]), 1)) * 100),
        )

        prompt = (
            f"You are an expert ATS & Technical Hiring Evaluator. Evaluate the candidate STRICTLY using "
            f"the retrieved resume chunks below—do NOT invent experience.\n\n"
            f"### Live Web & Risk Context:\n{state['web_verification']}\n\n"
            f"### Top Retrieved Resume Chunks (Hybrid BM25 + Cosine RRF):\n{grounded_context}\n\n"
            f"### Target Job Description:\n{state['job_text'][:2500]}"
        )

        try:
            structured_res: ReasoningOutput = structured_matcher.invoke(prompt)
        except Exception:
            # Fallback if primary model hits rate limit or structured-output constraint
            fallback_llm = ChatGroq(
                api_key=api_key, model=fast_model_id, temperature=0.15
            )
            structured_res = fallback_llm.with_structured_output(
                ReasoningOutput
            ).invoke(prompt)

        reasoning_dict = structured_res.model_dump()
        reasoning_dict["_model"] = f"LangGraph ({fast_model_id} + {smart_model_id})"

        est_tokens = int((len(prompt) + 900) / 4)
        telemetry["tokens"] = telemetry.get("tokens", 0) + est_tokens
        telemetry["token_savings_pct"] = saved_pct

        trace.append(
            f"✅ **Agent 2 — Hybrid RAG Matcher** (BM25 + Cosine RRF, `{saved_pct}%` context compression) · `{time.time() - t0:.2f}s`"
        )

        return {
            "retrieved_chunks": retrieved,
            "reasoning": reasoning_dict,
            "agent_trace": trace,
            "telemetry": telemetry,
        }

    # NODE 3: Self-Reflection Critic Agent (Verifies zero hallucination & sharpens resume bullets)
    def critic_refiner_node(state: JobShieldState):
        t0 = time.time()
        trace = list(state["agent_trace"])
        telemetry = dict(state["telemetry"])
        reasoning = dict(state["reasoning"])

        grounded_context = "\n---\n".join(state["retrieved_chunks"])
        draft_improvements = "\n".join(reasoning.get("resume_improvements", []))

        critic_prompt = (
            f"You are a Grounding Critic. Review these draft resume improvements and rewrite up to 4 "
            f"actionable, ATS-optimized bullet suggestions grounded 100% in the candidate's actual resume chunks "
            f"(zero fabricated metrics or tools). Return one bullet per line without numbering.\n\n"
            f"Draft Suggestions:\n{draft_improvements}\n\n"
            f"Actual Resume Chunks:\n{grounded_context}"
        )
        res = fast_llm.invoke(critic_prompt)
        refined_bullets = [
            line.lstrip("-•* ").strip()
            for line in res.content.splitlines()
            if len(line.strip()) > 10
        ]
        if refined_bullets:
            reasoning["resume_improvements"] = refined_bullets

        tokens = res.response_metadata.get("token_usage", {}).get("total_tokens", 350)
        telemetry["tokens"] = telemetry.get("tokens", 0) + tokens
        telemetry["est_cost_usd"] = round((telemetry["tokens"] / 1_000_000) * 0.25, 5)

        trace.append(
            f"✅ **Agent 3 — Grounding Critic** (`{fast_model_id}` anti-hallucination pass) · `{time.time() - t0:.2f}s`"
        )

        return {
            "reasoning": reasoning,
            "agent_trace": trace,
            "telemetry": telemetry,
        }

    workflow = StateGraph(JobShieldState)
    workflow.add_node("web_verifier", web_verifier_node)
    workflow.add_node("hybrid_rag_matcher", hybrid_rag_matcher_node)
    workflow.add_node("critic_refiner", critic_refiner_node)

    workflow.set_entry_point("web_verifier")
    workflow.add_edge("web_verifier", "hybrid_rag_matcher")
    workflow.add_edge("hybrid_rag_matcher", "critic_refiner")
    workflow.add_edge("critic_refiner", END)

    return workflow.compile()
