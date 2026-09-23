import os
import tempfile

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from resume.parser import extract_resume_text
from resume.cleaner import clean_resume_text
from analysis.analyzer import analyze_risk, analyze_reasoning

# --------------------------------------------------
# SETUP
# --------------------------------------------------

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.set_page_config(
    page_title="JobShield",
    page_icon="🛡️",
    layout="wide",
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
    "risk_result": None,
    "reasoning": None,
    "risk_confirmed": False,
    "analysis_started": False,
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
            AI Job Discovery & Safety Assistant
        </div>
        <div class="flow">
            Find → Verify → Match → Improve
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

uploaded_resume = st.file_uploader(
    "Upload your resume",
    type=["pdf", "docx"],
)

job_text = st.text_area(
    "💼 Paste Job Description",
    height=280,
    placeholder="Paste the complete job description here...",
)

risk_enabled = st.toggle(
    "🛡️ Enable Risk Analysis",
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
    st.session_state.risk_result = None
    st.session_state.reasoning = None
    st.session_state.risk_confirmed = False
    st.session_state.analysis_started = False

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

            st.write("🛡️ Checking job safety...")

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
risk_result = st.session_state.risk_result


# --------------------------------------------------
# HIGH-RISK GATE
# --------------------------------------------------

if (
    risk_enabled
    and risk_result
    and risk_result.get("risk_score", 0) >= 70
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
# 120B REASONING
# --------------------------------------------------

if st.session_state.reasoning is None and resume_text and saved_job_text:

    with st.status(
        "🤖 Running AI job matching...",
        expanded=True,
    ) as status:

        st.write("🧠 Comparing your resume with the job requirements...")

        reasoning = analyze_reasoning(
            resume_text,
            saved_job_text,
            risk_result,
            client,
        )

        st.session_state.reasoning = reasoning

        status.update(
            label="✅ Analysis complete!",
            state="complete",
            expanded=False,
        )


# --------------------------------------------------
# GET REASONING
# --------------------------------------------------

reasoning = st.session_state.reasoning

if reasoning is None:
    st.stop()


# --------------------------------------------------
# RISK ANALYSIS
# --------------------------------------------------

st.divider()

st.markdown(
    '<div class="section-title">🛡️ Job Risk Analysis</div>',
    unsafe_allow_html=True,
)

if risk_enabled:

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

        st.caption("Risk signal score based on detected indicators.")

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

match_score = reasoning.get(
    "match_score",
    0,
)

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

    st.caption("Based only on legitimate job requirements and resume evidence.")


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

    strengths = reasoning.get(
        "strengths",
        [],
    )

    if strengths:

        for item in strengths:

            st.markdown(f"**✓ {item['point']}**")

            st.markdown(
                f'<div class="evidence">' f'{item["evidence"]}' f"</div>",
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

    gaps = reasoning.get(
        "gaps",
        [],
    )

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

with st.expander(
    "🔎 Why This Matches",
):

    matches = reasoning.get(
        "why_this_matches",
        [],
    )

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

with st.expander(
    "📄 Resume Improvements",
):

    improvements = reasoning.get(
        "resume_improvements",
        [],
    )

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

with st.expander(
    "💡 Things to Consider",
):

    considerations = reasoning.get(
        "things_to_consider",
        [],
    )

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

st.caption(f"Reasoning model: {reasoning.get('_model', 'Unknown')}")

st.caption(
    "JobShield provides decision support based on the supplied resume and job description."
)
