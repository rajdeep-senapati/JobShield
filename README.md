# 🛡️ JobShield v2.0

### Agentic Job Verification & Hybrid-RAG Career Copilot

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-1C3C3C?logo=langchain&logoColor=white)](https://github.com/langchain-ai/langgraph)
[![Groq](https://img.shields.io/badge/Inference-Groq-F55036)](https://groq.com/)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Pydantic](https://img.shields.io/badge/Validation-Pydantic-E92063)](https://docs.pydantic.dev/)

> **Company Web Check → Hybrid Resume Retrieval → Structured Job Match → Grounded Critic**

JobShield is an AI-powered job verification and resume-matching application. It combines job-risk analysis, live company web search, hybrid retrieval over resume content, structured LLM reasoning, and a critic/refinement pass in a LangGraph workflow.

The goal is to help candidates investigate suspicious recruitment signals and understand how their documented experience relates to a job description—without treating safety concerns as qualifications or inventing candidate experience.

---

## ✨ Features

### 🛡️ Job risk analysis and confirmation

- Analyzes job descriptions for suspicious recruitment signals such as upfront fees, deposits, requests for sensitive identity or financial information, OTP requests, and unrealistic guarantees.
- Produces a **risk signal score from 0–100**. This is not a probability that a job is fraudulent.
- Derives the risk level and high-risk confirmation requirement deterministically from the validated score.
- Pauses the matching workflow when confirmation is required, allowing the user to review the explanations before continuing.

Risk analysis is a signal-detection aid, not proof that an employer or vacancy is fraudulent.

### 🌐 Company web verification

- Accepts an optional company name.
- Uses DuckDuckGo search results to gather a small set of public company, careers, and review references.
- Passes the retrieved snippets and job context to an LLM verification node for a concise summary.
- Displays the verification summary and execution trace in the Streamlit interface.

Web search coverage is limited and results can be incomplete or outdated. It does not independently certify a company's legitimacy.

### 🔎 Hybrid RAG resume matching

The matcher retrieves relevant resume sections before generating the job-fit analysis:

1. Splits the cleaned resume into paragraph-sized chunks.
2. Ranks chunks lexically using **BM25**.
3. Ranks chunks using **TF-IDF vectors and cosine similarity**.
4. Combines both rankings using **Reciprocal Rank Fusion (RRF)**.
5. Supplies the top retrieved chunks to the structured matching model.

This is a lightweight hybrid retrieval pipeline; the cosine retrieval uses TF-IDF rather than a neural embedding model.

### 🎯 Structured, evidence-oriented matching

The matching output includes:

- Match score and summary
- Strengths with resume evidence
- Gaps tied to job requirements
- Requirement-to-resume explanations
- Resume improvement suggestions
- Additional considerations

Pydantic structured output constrains the response shape. The prompts instruct the model to use explicit resume evidence, avoid invented skills or metrics, and keep safety-related requests separate from qualification matching.

### 🧪 Grounding critic

A third LangGraph node reviews draft resume-improvement suggestions against the retrieved resume chunks and refines them. This is an additional grounding pass, not a mathematical guarantee of zero hallucinations; users should review generated suggestions before using them.

### 📊 Execution trace and telemetry

The Streamlit interface surfaces:

- Pipeline token telemetry
- An estimated context-reduction percentage
- An estimated run-cost figure
- Per-node execution trace and latency
- Company web-verification summary
- Retrieved resume chunks

**Telemetry caveat:** token counts can include estimates when provider usage metadata is unavailable. The context-reduction figure is calculated from text length, not an exact tokenizer measurement. The displayed cost is an estimate based on the implementation's simplified rate assumption, not a billing quote from Groq.

### ⚡ Model selection and caching

- Queries the Groq models endpoint to select from configured fast and stronger model candidates, with fallback candidates if the lookup is unavailable.
- Uses a Streamlit data cache for repeated pipeline calls with identical inputs.
- Uses structured output for the main matching response.

---

## 🏗️ System Architecture

The application runs a sequential three-node LangGraph workflow after resume parsing and the optional risk-confirmation gate.

~~~mermaid
flowchart TD
    A[Streamlit UI] --> B[Resume PDF / DOCX]
    B --> C[Text Extraction & Cleaning]
    A --> D[Job Description + Company Name]
    D --> E[Job Risk Analysis]
    C --> F{High-risk confirmation required?}
    E --> F
    F -->|Yes| G[User Reviews & Confirms]
    F -->|No / Confirmed| H[LangGraph Workflow]
    G --> H
    H --> I[Agent 1: Company Web Verifier]
    I --> J[Agent 2: Hybrid RAG Matcher]
    J --> K[Agent 3: Grounding Critic]
    K --> L[Pydantic-shaped Match Output]
    L --> M[Results, Trace & Telemetry]
~~~

### The three LangGraph nodes

| Node | Responsibility | Implementation |
|---|---|---|
| **Agent 1 — Web Verifier** | Gather public company references and summarize them with job/risk context | DuckDuckGo Search (ddgs) + Groq chat model |
| **Agent 2 — Hybrid RAG Matcher** | Retrieve relevant resume chunks and generate structured job matching | BM25 + TF-IDF cosine similarity + RRF + Pydantic |
| **Agent 3 — Grounding Critic** | Review and refine resume-improvement suggestions against retrieved evidence | Groq chat model + retrieved resume chunks |

The graph is sequential: Web Verifier → Hybrid RAG Matcher → Grounding Critic.

---

## 🧠 Engineering Decisions

| Engineering concern | JobShield approach |
|---|---|
| Separate safety from qualification fit | Risk analysis and resume matching are separate stages; safety signals are not intended to affect the match score |
| Reduce irrelevant resume context | Hybrid retrieval selects a small set of relevant resume chunks |
| Combine lexical and vector-style retrieval | BM25 and TF-IDF cosine rankings are fused with RRF |
| Constrain model responses | Pydantic schemas define the expected structured matching output |
| Reduce unsupported resume edits | A critic node reviews improvement suggestions against retrieved resume text |
| Handle model availability | Runtime model discovery and fallback candidates are used |
| Avoid repeated pipeline work | Streamlit caching reuses results for identical cached inputs |
| Make execution easier to inspect | The UI exposes node traces, retrieved chunks, and approximate telemetry |

---

## 📂 Project Structure

~~~text
JobShield/
├── app.py                  # Streamlit UI, session state, risk gate, cache and telemetry
├── agent_pipeline.py       # LangGraph workflow, hybrid retrieval, model selection and critic
├── ai/
│   ├── reasoner.py         # Structured reasoning response parsing and validation
│   └── router.py           # Primary/fallback Groq model routing
├── analysis/
│   └── analyzer.py         # Risk-analysis integration and reasoning filters
├── risk/
│   └── analyzer.py         # Risk score generation and deterministic risk classification
├── resume/
│   ├── parser.py           # PDF and DOCX text extraction
│   └── cleaner.py          # Resume text normalization
├── job/
│   ├── loader.py           # Job data loading
│   └── schema.py           # Job data model
├── data/                   # Project data
├── requirements.txt        # Python dependencies
└── README.md
~~~

---

## 🛠️ Tech Stack

- **Language:** Python
- **Orchestration:** LangGraph
- **LLM inference:** Groq, LangChain-Groq
- **Models:** Runtime-selected Groq chat models (candidate list configured in agent_pipeline.py)
- **Structured validation:** Pydantic
- **Retrieval:** rank-bm25, scikit-learn TF-IDF, cosine similarity, NumPy
- **Web search:** DuckDuckGo Search (ddgs)
- **UI:** Streamlit
- **Resume parsing:** pypdf, python-docx
- **Configuration:** python-dotenv

---

## 🚀 Quickstart

### 1. Clone the repository

~~~bash
git clone https://github.com/rajdeep-senapati/JobShield.git
cd JobShield
~~~

### 2. Create and activate a virtual environment

**Windows PowerShell**

~~~powershell
python -m venv .jobshield-env
.\.jobshield-env\Scripts\Activate.ps1
~~~

**macOS / Linux**

~~~bash
python -m venv .jobshield-env
source .jobshield-env/bin/activate
~~~

### 3. Install dependencies

~~~bash
python -m pip install --upgrade pip
pip install -r requirements.txt
~~~

### 4. Configure the Groq API key

Create a .env file in the repository root:

~~~env
GROQ_API_KEY=your_groq_api_key
~~~

Never commit your API key. The repository's .gitignore excludes local environment files and Streamlit secrets.

### 5. Run JobShield

~~~bash
streamlit run app.py
~~~

Open the local URL printed by Streamlit.

---

## ☁️ Deploy on Streamlit Community Cloud

1. Push the project to GitHub.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) with GitHub.
3. Create an app using this repository, the main branch, and app.py as the entry point.
4. In the app's **Settings → Secrets**, add:

~~~toml
GROQ_API_KEY = "your_groq_api_key"
~~~

5. Deploy the app.

Check the current [Streamlit Community Cloud documentation](https://docs.streamlit.io/deploy/streamlit-community-cloud) for availability, resource limits, and deployment settings.

---

## 🧪 Validation Scenarios

Use these scenarios when manually validating a deployment:

### High-risk job description

Use a sample posting containing suspicious requests such as a registration payment, security deposit, OTP, or sensitive financial details.

Expected flow:

~~~text
Resume + Job Description
        ↓
Risk Analysis
        ↓
High-risk score
        ↓
Confirmation screen
        ↓
User chooses to continue
        ↓
LangGraph matching workflow
~~~

### Standard job description

Use a conventional job description with explicit skills and responsibilities.

Expected flow:

~~~text
Resume + Job Description
        ↓
Risk Analysis
        ↓
Company Web Verification
        ↓
Hybrid Resume Retrieval
        ↓
Structured Match + Grounding Critic
        ↓
Strengths, Gaps & Improvements
~~~

The repository should be treated as an actively developed project. Run and verify these scenarios in the target environment; do not interpret example scores as guaranteed outputs.

---

## ⚠️ Limitations

- Company verification depends on a limited set of public search results and LLM interpretation; it is not a comprehensive background check.
- A risk score indicates detected signals, not a definitive scam classification or probability.
- Hybrid retrieval uses BM25 and TF-IDF cosine similarity, not a neural embedding database.
- The critic is a second-pass review and cannot guarantee that every generated statement is correct.
- Telemetry includes estimates where exact provider usage is unavailable; cost is approximate.
- Matching quality depends on the clarity and completeness of the uploaded resume and job description.
- Job descriptions are pasted by the user; automated job discovery and full job-page extraction are not currently part of the documented workflow.
- JobShield is decision support and does not replace independent employer verification or the candidate's judgment.

---

## 🔮 Potential Next Steps

- Add automated unit and integration tests for retrieval, schemas, risk gating, and model fallback.
- Add source citations and stronger evidence checks for web verification.
- Evaluate retrieval quality with a labelled resume/JD test set.
- Add robust error handling and retry policies for external search and model calls.
- Add persistence for saved analyses and user history.
- Track actual token usage and provider-specific pricing more precisely.
- Add job URL ingestion and controlled page extraction.

---

## 🧪 RAG Evaluation & Retrieval Ablation (`rag_eval.py`)

Benchmarked across multi-domain resume/JD pairs (`k=2`) comparing standalone lexical and vector retrievers against **Hybrid Reciprocal Rank Fusion (BM25 + Cosine RRF)**, paired with an automated **LLM-as-a-Judge Faithfulness** check:

| Retrieval Strategy | Precision@2 | Recall@2 | MRR | Avg Latency |
| :--- | :---: | :---: | :---: | :---: |
| Sparse Only (`BM25`) | 0.500 | 0.500 | 0.833 | 1.22 ms |
| Dense/Vector Only (`TF-IDF Cosine`) | 0.667 | 0.667 | 0.833 | 18.07 ms |
| **Hybrid RAG (`BM25 + Cosine RRF`)** | **0.667** | **0.667** | **0.833** | **3.63 ms** |

* **Generation Faithfulness Score:** `1.00 / 1.00` (`0` hallucinated skills or metrics verified by automated grounding judge across LangGraph critic outputs).
* **End-to-End Pipeline Unit Cost:** `2,262` tokens (`$0.00057` per full multi-agent evaluation).
* **Key Takeaway:** Hybrid RRF improves Precision@2 and Recall@2 by **+33.4%** over pure lexical BM25 while keeping retrieval latency at **3.63 ms**—a 5x speedup over cold-start dense TF-IDF scoring alone.
* Reproduce locally via `python rag_eval.py`.

---

## 👤 Author

**Rajdeep Senapati**

B.Tech — Computer Science (Data Science)  
Heritage Institute of Technology, Kolkata

- [GitHub](https://github.com/rajdeep-senapati)
- [LinkedIn](https://www.linkedin.com/in/rajdeep-senapati)
- [Portfolio](https://rajdeep-senapati.vercel.app)

---

## 📌 Project Status

**JobShield v2.0 — Active Development**

The repository contains a Streamlit application with a risk-analysis and confirmation stage, a sequential three-node LangGraph workflow, hybrid resume retrieval, structured job matching, a grounding-critic pass, and execution telemetry.
