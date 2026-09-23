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

st.title("🛡️ JobShield")
st.subheader("AI Job Discovery & Safety Assistant")

st.markdown("**Find → Verify → Match → Improve**")

st.divider()


# --------------------------------------------------
# INPUTS
# --------------------------------------------------

uploaded_resume = st.file_uploader(
    "📄 Upload your resume",
    type=["pdf", "docx"],
)

job_text = st.text_area(
    "💼 Paste Job Description",
    height=300,
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

    # Save inputs in session state
    st.session_state.job_text = job_text

    # --------------------------------------------------
    # RESUME PROCESSING
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

        # --------------------------------------------------
        # RISK ANALYSIS
        # --------------------------------------------------

        if risk_enabled:

            st.write("🛡️ Checking job safety...")
            st.write("🔍 Running risk analysis...")

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

    # Force Streamlit to rerun so the risk gate
    # can use the persisted session state.
    st.rerun()


# --------------------------------------------------
# STOP IF NO ANALYSIS EXISTS
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

    st.error(f"⚠️ High Risk Signal Score: " f"{risk_result['risk_score']}/100")

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

        st.write("🧠 Analyzing resume against job requirements...")

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
# RISK RESULT
# --------------------------------------------------

st.divider()

st.header("🛡️ Job Risk Analysis")

if risk_enabled:

    st.metric(
        "Risk Score",
        f"{risk_result['risk_score']}/100",
    )

    st.caption("Risk signal score based on detected indicators.")

    if risk_result.get("signals"):

        for explanation in risk_result.get("explanations", []):
            st.warning(explanation)

    else:

        st.success("No significant risk signals were detected.")

else:

    st.info("Risk analysis was disabled.")


# --------------------------------------------------
# JOB MATCH
# --------------------------------------------------

st.divider()

st.header("🎯 Job Match")

st.metric(
    "Match Score",
    f"{reasoning['match_score']}/100",
)

st.write(reasoning["match_summary"])


with st.expander("💪 Strengths"):

    for item in reasoning["strengths"]:

        st.markdown(f"**{item['point']}**")

        st.caption(item["evidence"])


with st.expander("⚠️ Gaps"):

    for item in reasoning["gaps"]:

        st.markdown(f"**{item['point']}**")

        st.caption(f"Job requirement: " f"{item['job_requirement']}")


with st.expander("🔎 Why This Matches"):

    for item in reasoning["why_this_matches"]:

        st.write(f"• {item}")


with st.expander("📄 Resume Improvements"):

    for item in reasoning["resume_improvements"]:

        st.write(f"• {item}")


with st.expander("💡 Things to Consider"):

    for item in reasoning["things_to_consider"]:

        st.write(f"• {item}")


st.caption(f"Reasoning model: {reasoning['_model']}")
