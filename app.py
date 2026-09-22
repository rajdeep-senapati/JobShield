import os
import tempfile

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from resume.parser import extract_resume_text
from resume.cleaner import clean_resume_text
from analysis.analyzer import analyze_job

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


st.set_page_config(
    page_title="JobShield",
    page_icon="🛡️",
    layout="wide",
)


st.title("🛡️ JobShield")
st.subheader("AI Job Discovery & Safety Assistant")

st.markdown("**Find → Verify → Match → Improve**")

st.divider()


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


if st.button("🔍 Analyze Job", use_container_width=True):

    if not uploaded_resume:
        st.warning("Please upload your resume first.")
        st.stop()

    if not job_text.strip():
        st.warning("Please paste a job description first.")
        st.stop()

    with st.spinner("Processing resume..."):

        suffix = os.path.splitext(uploaded_resume.name)[1]

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:

            temp_file.write(uploaded_resume.getbuffer())

            resume_path = temp_file.name

        resume_text = extract_resume_text(resume_path)

        cleaned_resume_text = clean_resume_text(resume_text)

    # Risk analysis
    result = analyze_job(
        cleaned_resume_text,
        job_text,
        client,
        risk_enabled,
    )

    # High-risk gate
    if risk_enabled and result["risk"]["risk_score"] >= 70:

        risk = result["risk"]

        st.error(f"⚠️ High Risk Signal Score: " f"{risk['risk_score']}/100")

        for explanation in risk["explanations"]:
            st.warning(explanation)

        continue_analysis = st.button(
            "Continue to Job Matching",
            key="continue_risk",
        )

        if not continue_analysis:
            st.stop()

    st.success("Risk analysis complete.")

    st.divider()

    # Risk result
    if risk_enabled:

        st.header("🛡️ Job Risk Analysis")

        risk = result["risk"]

        st.metric("Risk Score", f"{risk['risk_score']}/100")

        st.caption("Risk signal score based on detected indicators.")

        if risk["signals"]:

            for explanation in risk["explanations"]:
                st.warning(explanation)

        else:

            st.success("No significant risk signals were detected.")

    else:

        st.header("🛡️ Job Risk Analysis")

        st.info("Risk analysis was disabled.")

    st.divider()

    # Temporary status
    st.header("🤖 Job Analysis")

    st.info(
        "Risk analysis is complete. "
        "The GPT-OSS 120B reasoning stage will be connected next."
    )