# 🛡️ JobShield

### AI Job Discovery & Safety Assistant

> **Find → Verify → Match → Improve**

JobShield is an AI-powered job analysis assistant that helps candidates evaluate job descriptions for potential safety risks and understand how well their resume matches legitimate job requirements.

Instead of treating every job posting as trustworthy, JobShield separates **job safety analysis** from **candidate-job matching** so that suspicious recruitment signals don't distort the actual qualification match.

---

## 🚀 What JobShield Does

JobShield follows a simple four-stage workflow:

**Find → Verify → Match → Improve**

```text
                    ┌─────────────────┐
                    │   Your Resume   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Resume Parsing  │
                    │  & Cleaning    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Job Description │
                    └────────┬────────┘
                             │
                  ┌──────────┴──────────┐
                  ▼                     ▼
          ┌───────────────┐     ┌───────────────┐
          │ Risk Analysis │     │ Job Matching  │
          │   20B Model   │     │   120B Model  │
          └───────┬───────┘     └───────┬───────┘
                  │                     │
                  ▼                     ▼
          Risk Signal Score       Match Score
                  │                     │
                  └──────────┬──────────┘
                             ▼
                    ┌─────────────────┐
                    │ Explain Results │
                    │ & Improvements  │
                    └─────────────────┘
```

---

## ✨ Features

### 🛡️ Job Risk Analysis

Detects potentially suspicious recruitment patterns such as:

* Upfront registration fees
* Security deposits
* Requests for sensitive identity information
* Requests for financial information
* OTP requests
* Unrealistic guaranteed income
* Other suspicious recruitment signals

The result is presented as a **risk signal score from 0–100**, not as a probability that a job is a scam.

High-risk results trigger an additional confirmation step before the AI performs the detailed job matching.

---

### 🎯 AI Job Matching

JobShield compares the resume against the legitimate requirements of the job.

It provides:

* Match score
* Match summary
* Strengths
* Gaps
* Requirement-to-resume connections
* Resume improvement suggestions
* Additional considerations

The matching system is designed to avoid treating safety-related requests such as fees, deposits, OTPs, or sensitive personal information as job qualifications.

---

### 📄 Resume Processing

Supports:

* PDF resumes
* DOCX resumes

The resume is processed using Python before being passed to the reasoning model.

The pipeline includes:

```text
Resume
   ↓
Text Extraction
   ↓
Text Cleaning
   ↓
Clean Resume Representation
```

No LLM is required for the initial resume extraction and cleaning stage.

---

### 🤖 Two-Stage AI Architecture

JobShield uses different models for different responsibilities.

**Risk Analysis**

```text
openai/gpt-oss-20b
```

Used specifically for identifying job safety/risk signals.

**Job Reasoning**

```text
openai/gpt-oss-120b
```

Used for deeper resume-to-job reasoning and evidence-based matching.

This separation prevents safety concerns from becoming part of the candidate's qualification score.

---

## 🧠 Matching Philosophy

JobShield follows several grounding principles:

* Match only against legitimate job requirements.
* Use information explicitly present in the resume.
* Do not invent candidate skills or experience.
* Do not infer experience simply from a technology name or job title.
* Every strength should have supporting resume evidence.
* Every gap should correspond to an explicit job requirement.
* Safety-related requests should not affect the match score.
* Resume improvements should focus on presenting or clarifying existing evidence.
* The system provides decision support rather than making the final application decision for the user.

---

## 🔬 Example: High-Risk Job

Example job description containing:

```text
₹2,000 registration fee
Security deposit
Aadhaar and PAN details
Bank account information
OTP verification
₹5,000/day guaranteed income
No experience required
```

JobShield identified:

```text
Risk Score: 90/100
```

The system then displayed the detected risk signals and required confirmation before continuing to detailed job matching.

Because the posting contained no meaningful legitimate qualifications to compare against the resume, the resulting:

```text
Match Score: 0/100
```

This demonstrates the separation between **job safety** and **candidate qualification matching**.

---

## 📊 Example: Legitimate Data Analyst Job

For a normal Data Analyst role, JobShield can identify legitimate matches such as:

```text
Resume Evidence
      ↓
Python
SQL
Power BI
Data Analysis
Azure
Dashboards
      ↓
Job Requirements
      ↓
Evidence-Based Match
```

Example output:

```text
Risk Score: 0/100

Match Score: 75/100
```

The system can then identify both relevant strengths and explicit requirements where the resume lacks direct evidence.

---

## 🏗️ Project Architecture

```text
JobShield/
│
├── app.py
│
├── ai/
│   ├── reasoner.py
│   ├── router.py
│   └── __init__.py
│
├── analysis/
│   ├── analyzer.py
│   └── __init__.py
│
├── job/
│   ├── loader.py
│   ├── schema.py
│   └── __init__.py
│
├── resume/
│   ├── parser.py
│   ├── cleaner.py
│   ├── profile.py
│   └── __init__.py
│
├── risk/
│   ├── analyzer.py
│   └── __init__.py
│
└── data/
    └── ...
```

---

## 🛠️ Tech Stack

### AI / LLM

* Groq
* `openai/gpt-oss-20b`
* `openai/gpt-oss-120b`

### Backend

* Python

### AI Application

* Streamlit

### Resume Processing

* PyPDF
* python-docx
* Python-based text cleaning

### Environment & Configuration

* python-dotenv

---

## ⚙️ Installation

Clone the repository:

```bash
git clone https://github.com/rajdeep-senapati/JobShield.git
cd JobShield
```

Create a virtual environment:

### Windows PowerShell

```powershell
python -m venv .jobshield-env
.\.jobshield-env\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
```

Do not commit your API key to GitHub.

Make sure `.env` is included in `.gitignore`.

---

## ▶️ Run Locally

Start the Streamlit application:

```bash
streamlit run app.py
```

Then open the local Streamlit URL shown in the terminal.

---

## 🧪 Testing

JobShield has been tested with two primary scenarios.

### High-Risk Job

Expected behavior:

```text
Risk Analysis
      ↓
High Risk Signal
      ↓
Confirmation Required
      ↓
User Confirms
      ↓
Job Matching
```

### Normal Job

Expected behavior:

```text
Risk Analysis
      ↓
Low Risk
      ↓
Job Matching
      ↓
Strengths + Gaps + Improvements
```

The system has also been tested for model-generated JSON containing additional text and uses structured parsing to extract the valid JSON response.

---

## 🚧 Current Limitations

* Job descriptions are currently provided manually by the user.
* Job URL verification is not yet implemented.
* Risk detection identifies signals but does not prove that a job is fraudulent.
* Matching quality depends on the information available in the resume and job description.
* The system does not replace independent verification of an employer or job posting.

---

## 🔮 Future Improvements

Planned directions include:

* Job URL input and extraction
* Employer and job-source verification
* Automated job discovery
* More robust job-posting validation
* Resume-to-JD comparison visualizations
* Job history and saved analyses
* Improved deployment and production infrastructure

---

## 🎯 Design Goal

JobShield is designed around one principle:

> **Help candidates understand a job before they apply.**

The system separates:

**Safety signals** → *Is there anything suspicious to investigate?*

from

**Qualification matching** → *How does the candidate's documented experience relate to the legitimate requirements?*

This keeps the two problems separate and makes the resulting analysis easier to understand.

---

## 👨‍💻 Author

**Rajdeep Senapati**

B.Tech — Computer Science (Data Science)

Heritage Institute of Technology, Kolkata

[GitHub](https://github.com/rajdeep-senapati)

[LinkedIn](https://www.linkedin.com/in/rajdeep-senapati)

---

## 📌 Status

**JobShield MVP — Active Development**

The core risk-analysis, high-risk confirmation, AI job-matching, evidence-based reasoning, and Streamlit interface are implemented.
