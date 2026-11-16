import os
import tempfile

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from resume.parser import extract_resume_text
from resume.cleaner import clean_resume_text
from analysis.analyzer import analyze_risk
from agent_pipeline import build_jobshield_graph

# --------------------------------------------------
# SETUP
# --------------------------------------------------

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        api_key = None

if not api_key:
    st.error(
        "GROQ_API_KEY is missing. Configure it in your environment or app secrets."
    )
    st.stop()

client = Groq(api_key=api_key)

st.set_page_config(
    page_title="JobShield",
    page_icon="🛡️",
    layout="wide",
)


# --------------------------------------------------
# CACHED MULTI-AGENT RUNNER (Zero-Cost Repeat Runs)
# --------------------------------------------------


@st.cache_data(show_spinner=False)
def run_cached_agent_pipeline(
    resume_text: str,
    job_text: str,
    company_name: str,
    risk_result: dict,
    _api_key: str,
) -> dict:
    graph = build_jobshield_graph(_api_key)
    return graph.invoke(
        {
            "resume_text": resume_text,
            "job_text": job_text,
            "company_name": company_name,
            "risk_result": risk_result or {},
            "web_verification": "",
            "retrieved_chunks": [],
            "reasoning": {},
            "agent_trace": [],
            "telemetry": {},
        }
    )


# --------------------------------------------------
# CUSTOM UI
# --------------------------------------------------

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1200px;
        }

        .hero {
            padding: 1.5rem 0 1rem 0;
        }

        .hero-title {
            font-size: 2.6rem;
            font-weight: 700;
            margin-bottom: 0.2rem;
        }

        .hero-subtitle {
            font-size: 1.15rem;
            opacity: 0.75;
            margin-bottom: 0.5rem;
        }

        .flow {
            font-size: 0.95rem;
            font-weight: 600;
            opacity: 0.8;
        }

        .section-title {
            font-size: 1.45rem;
            font-weight: 700;
            margin-top: 1rem;
            margin-bottom: 0.8rem;
        }

        .score-label {
            font-size: 0.85rem;
            font-weight: 600;
            opacity: 0.7;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .score-value {
            font-size: 2.4rem;
            font-weight: 700;
            margin-top: -0.2rem;
        }

        .evidence {
            font-size: 0.9rem;
            opacity: 0.75;
            margin-top: -0.2rem;
        }

        .empty-state {
            padding: 0.8rem 1rem;
            border-radius: 0.5rem;
            background: rgba(128, 128, 128, 0.08);
            opacity: 0.75;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

defaults = {
    "resume_text": None,
    "job_text": None,
    "company_name": "",
    "risk_result": None,
    "reasoning": None,
    "agent_state": None,
    "risk_confirmed": False,
    "analysis_started": False,
    "risk_analysis_enabled": False,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">🛡️ JobShield</div>
        <div class="hero-subtitle">
            Agentic Job Verification & Hybrid-RAG Career Copilot
        </div>
        <div class="flow">
            Web Verify (Tool Use) → Hybrid RAG (BM25 + Cosine) → Match → Grounded Critic
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()


# --------------------------------------------------
# INPUTS
# --------------------------------------------------

st.subheader("📄 Resume & Job")

col_in1, col_in2 = st.columns([2, 1])

with col_in1:
    uploaded_resume = st.file_uploader(
        "Upload your resume",
        type=["pdf", "docx"],
    )

with col_in2:
    company_name = st.text_input(
        "🏢 Company Name (for live web check)",
        placeholder="e.g., Stripe, Acme Corp...",
    )

job_text = st.text_area(
    "💼 Paste Job Description",
    height=260,
    placeholder="Paste the complete job description here...",
)

risk_enabled = st.toggle(
    "🛡️ Enable Risk & Web Verification",
    value=True,
    help="Disable this if you have already verified the job and want faster analysis.",
)


# --------------------------------------------------
# ANALYZE BUTTON
# --------------------------------------------------

if st.button(
    "🔍 Analyze Job",
    use_container_width=True,
    type="primary",
):
    # Reset previous analysis
    st.session_state.resume_text = None
    st.session_state.job_text = None
    st.session_state.company_name = company_name
    st.session_state.risk_result = None
    st.session_state.reasoning = None
    st.session_state.agent_state = None
    st.session_state.risk_confirmed = False
    st.session_state.analysis_started = False
    st.session_state.risk_analysis_enabled = risk_enabled

    # Validate inputs
    if not uploaded_resume:
        st.warning("Please upload your resume first.")
        st.stop()

    if not job_text.strip():
        st.warning("Please paste a job description first.")
        st.stop()

    st.session_state.job_text = job_text

    # --------------------------------------------------
    # RESUME + RISK ANALYSIS
    # --------------------------------------------------

    with st.status(
        "🔄 Preparing analysis...",
        expanded=True,
    ) as status:
        st.write("📄 Processing resume...")

        suffix = os.path.splitext(uploaded_resume.name)[1]

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:
            temp_file.write(uploaded_resume.getbuffer())
            resume_path = temp_file.name

        try:
            resume_text = extract_resume_text(resume_path)
            cleaned_resume_text = clean_resume_text(resume_text)
            st.session_state.resume_text = cleaned_resume_text
        finally:
            if os.path.exists(resume_path):
                os.remove(resume_path)

        if risk_enabled:
            st.write("🛡️ Running heuristic job safety scan...")
            risk_result = analyze_risk(
                job_text,
                client,
            )
            st.session_state.risk_result = risk_result

            status.update(
                label="🛡️ Risk analysis complete",
                state="complete",
                expanded=False,
            )
        else:
            st.session_state.risk_result = {"risk_analysis_enabled": False}

            status.update(
                label="⏭️ Risk analysis skipped",
                state="complete",
                expanded=False,
            )

    st.session_state.analysis_started = True
    st.rerun()


# --------------------------------------------------
# STOP IF NO ANALYSIS
# --------------------------------------------------

if not st.session_state.analysis_started:
    st.stop()


# --------------------------------------------------
# LOAD SESSION DATA
# --------------------------------------------------

resume_text = st.session_state.resume_text
saved_job_text = st.session_state.job_text
saved_company = st.session_state.company_name
risk_result = st.session_state.risk_result


# --------------------------------------------------
# HIGH-RISK GATE
# --------------------------------------------------

if (
    st.session_state.risk_analysis_enabled
    and risk_result
    and risk_result.get("requires_confirmation", False)
    and not st.session_state.risk_confirmed
):
    st.divider()
    st.header("🛡️ Job Safety Check")

    risk_score = risk_result["risk_score"]
    st.error(f"⚠️ High Risk Signal Score: {risk_score}/100")

    for explanation in risk_result.get("explanations", []):
        st.warning(explanation)

    st.warning("Review these signals before continuing.")

    if st.button(
        "Continue to Job Matching",
        key="continue_risk",
        type="primary",
        use_container_width=True,
    ):
        st.session_state.risk_confirmed = True
        st.rerun()

    st.stop()


# --------------------------------------------------
# LANGGRAPH MULTI-AGENT + HYBRID RAG PIPELINE
# --------------------------------------------------

if st.session_state.reasoning is None and resume_text and saved_job_text:
    with st.status(
        "🤖 Executing LangGraph Multi-Agent & Hybrid RAG Pipeline...",
        expanded=True,
    ) as status:
        st.write("🌐 Agent 1: Verifying company legitimacy via live web search...")
        st.write(
            "🔎 Agent 2: Running Hybrid RAG (BM25 + Cosine RRF) retrieval & matching..."
        )
        st.write(
            "🛡️ Agent 3: Grounding Critic verifying zero-hallucination resume edits..."
        )

        agent_state = run_cached_agent_pipeline(
            resume_text,
            saved_job_text,
            saved_company,
            risk_result,
            api_key,
        )

        st.session_state.agent_state = agent_state
        st.session_state.reasoning = agent_state["reasoning"]

        status.update(
            label="✅ Multi-Agent Analysis Complete!",
            state="complete",
            expanded=False,
        )


# --------------------------------------------------
# GET REASONING & TELEMETRY
# --------------------------------------------------

reasoning = st.session_state.reasoning
agent_state = st.session_state.agent_state or {}
telemetry = agent_state.get("telemetry", {})

if reasoning is None:
    st.stop()


# --------------------------------------------------
# TELEMETRY & AGENT EXECUTION TRACE BANNER
# --------------------------------------------------

st.divider()

t_col1, t_col2, t_col3 = st.columns(3)
t_col1.metric("Total Pipeline Tokens", f"{telemetry.get('tokens', 0):,}")
t_col2.metric("Hybrid RAG Context Saved", f"{telemetry.get('token_savings_pct', 0)}%")
t_col3.metric("Est. Run Cost", f"${telemetry.get('est_cost_usd', 0.0004)}")

with st.expander("⚙️ View LangGraph Agent Execution Trace & Retrieved RAG Chunks"):
    for step in agent_state.get("agent_trace", []):
        st.markdown(step)

    if agent_state.get("web_verification"):
        st.markdown("**Live Web Verification Summary:**")
        st.info(agent_state["web_verification"])

    chunks = agent_state.get("retrieved_chunks", [])
    if chunks:
        st.markdown(
            f"**Top {len(chunks)} Resume Chunks Retrieved (BM25 + Cosine RRF):**"
        )
        for idx, chunk in enumerate(chunks, 1):
            st.code(chunk, language="text")


# --------------------------------------------------
# RISK ANALYSIS
# --------------------------------------------------

st.divider()

st.markdown(
    '<div class="section-title">🛡️ Job Risk Analysis</div>',
    unsafe_allow_html=True,
)

if st.session_state.risk_analysis_enabled:
    risk_score = risk_result.get("risk_score", 0)
    col1, col2 = st.columns([1, 3])

    with col1:
        st.markdown(
            '<div class="score-label">Risk Score</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="score-value">{risk_score}/100</div>',
            unsafe_allow_html=True,
        )

    with col2:
        st.progress(risk_score / 100)
        st.caption("Risk signal score based on heuristic indicators & live web check.")

    explanations = risk_result.get("explanations", [])

    if explanations:
        for explanation in explanations:
            st.warning(f"• {explanation}")
    else:
        st.success("✓ No significant risk signals were detected.")
else:
    st.info("Risk analysis was disabled for this analysis.")


# --------------------------------------------------
# JOB MATCH
# --------------------------------------------------

st.divider()

st.markdown(
    '<div class="section-title">🎯 Job Match</div>',
    unsafe_allow_html=True,
)

match_score = reasoning.get("match_score", 0)
col1, col2 = st.columns([1, 3])

with col1:
    st.markdown(
        '<div class="score-label">Match Score</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="score-value">{match_score}/100</div>',
        unsafe_allow_html=True,
    )

with col2:
    st.progress(match_score / 100)
    st.caption(
        "Based only on legitimate job requirements and retrieved resume evidence."
    )

st.info(
    reasoning.get(
        "match_summary",
        "No match summary was generated.",
    )
)


# --------------------------------------------------
# STRENGTHS
# --------------------------------------------------

with st.expander(
    "💪 Strengths",
    expanded=True,
):
    strengths = reasoning.get("strengths", [])

    if strengths:
        for item in strengths:
            st.markdown(f"**✓ {item['point']}**")
            st.markdown(
                f'<div class="evidence">{item["evidence"]}</div>',
                unsafe_allow_html=True,
            )
            st.divider()
    else:
        st.markdown(
            '<div class="empty-state">'
            "No direct strengths were identified for this role."
            "</div>",
            unsafe_allow_html=True,
        )


# --------------------------------------------------
# GAPS
# --------------------------------------------------

with st.expander(
    "⚠️ Gaps",
    expanded=True,
):
    gaps = reasoning.get("gaps", [])

    if gaps:
        for item in gaps:
            st.markdown(f"**⚠ {item['point']}**")
            st.markdown(
                f'<div class="evidence">'
                f'Job requirement: {item["job_requirement"]}'
                f"</div>",
                unsafe_allow_html=True,
            )
            st.divider()
    else:
        st.markdown(
            '<div class="empty-state">'
            "No significant legitimate gaps were identified."
            "</div>",
            unsafe_allow_html=True,
        )


# --------------------------------------------------
# WHY THIS MATCHES
# --------------------------------------------------

with st.expander("🔎 Why This Matches"):
    matches = reasoning.get("why_this_matches", [])

    if matches:
        for item in matches:
            st.markdown(f"• {item}")
    else:
        st.markdown(
            '<div class="empty-state">'
            "No direct requirement-to-resume connections were identified."
            "</div>",
            unsafe_allow_html=True,
        )


# --------------------------------------------------
# RESUME IMPROVEMENTS
# --------------------------------------------------

with st.expander("📄 Grounded Resume Improvements", expanded=True):
    improvements = reasoning.get("resume_improvements", [])

    if improvements:
        for item in improvements:
            st.markdown(f"• {item}")
    else:
        st.markdown(
            '<div class="empty-state">'
            "No role-specific resume improvements were identified."
            "</div>",
            unsafe_allow_html=True,
        )


# --------------------------------------------------
# THINGS TO CONSIDER
# --------------------------------------------------

with st.expander("💡 Things to Consider"):
    considerations = reasoning.get("things_to_consider", [])

    if considerations:
        for item in considerations:
            st.markdown(f"• {item}")
    else:
        st.markdown(
            '<div class="empty-state">'
            "No additional considerations were identified."
            "</div>",
            unsafe_allow_html=True,
        )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(f"Reasoning engine: {reasoning.get('_model', 'Unknown')}")
st.caption(
    "JobShield provides grounded decision support based on retrieved resume evidence, live web verification, and the supplied job description."
)
