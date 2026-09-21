import os
import json
import tempfile

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from resume.parser import extract_resume_text
from resume.cleaner import clean_resume_text
from resume.extractor import extract_resume_profile
from analysis.analyzer import analyze_job
from job.extractor import extract_job_profile
from job.loader import load_job_from_profile

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

if st.button("🔍 Analyze Job", use_container_width=True):

    if not uploaded_resume:
        st.warning("Please upload your resume first.")
        st.stop()

    if not job_text.strip():
        st.warning("Please paste a job description first.")
        st.stop()

    with st.spinner("Analyzing your resume and job..."):

        # Save uploaded resume temporarily
        suffix = os.path.splitext(uploaded_resume.name)[1]

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:

            temp_file.write(uploaded_resume.getbuffer())
            resume_path = temp_file.name

        # Resume processing
        resume_text = extract_resume_text(resume_path)
        cleaned_text = clean_resume_text(resume_text)

        resume_profile = extract_resume_profile(cleaned_text, client)

        # Temporary job object
        job_profile = extract_job_profile(job_text, client)

        job = load_job_from_profile(job_profile)

        with st.expander("🔍 Debug: Extracted Data"):
            st.subheader("Extracted JD Profile")
            st.json(job_profile)

            st.subheader("Extracted Resume Profile")
            st.json(resume_profile)

        # Run existing analysis pipeline
        result = analyze_job(
            resume_profile,
            job,
            client,
        )

    st.success("Analysis complete!")

    st.divider()

    # Match
    st.header("🎯 Job Match")

    match = result["match"]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Match Score", f"{match['match_score']}%")

    with col2:
        st.metric("Skill Match", f"{match['skill_match']['skill_match_percentage']}%")

    with col3:
        st.metric("Title Match", "Yes" if match["title_match"]["title_match"] else "No")

    st.subheader("Matched Skills")
    st.write(", ".join(match["skill_match"]["matched_skills"]) or "None detected")

    st.subheader("Missing Skills")
    st.write(", ".join(match["skill_match"]["missing_skills"]) or "None detected")

    st.divider()

    # Risk
    st.header("🛡️ Job Risk Signals")

    risk = result["risk"]

    st.metric("Risk Level", risk["risk_level"].upper())

    if risk["risk_signals"]:
        for explanation in risk["risk_explanations"]:
            st.warning(explanation)
    else:
        st.success("No predefined risk indicators were detected.")

    st.divider()

    # AI reasoning
    st.header("🤖 AI Analysis")

    reasoning = result["reasoning"]

    st.subheader("Summary")
    st.write(reasoning["summary"])

    st.subheader("Why It Matches")
    for item in reasoning["why_it_matches"]:
        st.write(f"• {item}")

    st.subheader("Resume Improvements")
    for item in reasoning["resume_improvements"]:
        st.write(f"• {item}")

    st.subheader("Things to Consider")
    st.info(reasoning["recommendation_context"])
