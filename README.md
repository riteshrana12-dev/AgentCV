# ⚡ ATS Optimization Engine (`ai-engine`)

> **Work In Progress** 🚧  
> _This microservice is currently under active development and testing. Core workflows, schemas, and node logic are continuously being optimized for production deployment._

---

## 📌 Project Overview

The **ATS Optimization Engine** is an asynchronous, high-performance AI microservice designed to evaluate, optimize, and generate job application packages. Built on **FastAPI**, **LangGraph**, and **Gemini 2.5 Flash**, the system accepts candidate resumes alongside target job descriptions to produce tailored resume bullets, skill gap analyses, outreach collateral, and interactive interview preparation workflows.

To ensure production scalability and security, all incoming document files (`.pdf`, `.docx`, `.doc`) are processed entirely **in-memory** from cloud storage, avoiding local disk writes and transient file artifacts.

---

## 🔑 Key Capabilities

- **In-Memory Byte Processing**: Directly reads and parses document buffers retrieved from Supabase Storage without writing files to local disk storage.
- **Hybrid ATS Evaluation**: Combines deterministic natural language processing (`spaCy`, `rapidfuzz`) for exact keyword and formatting extraction with **Gemini 2.5 Flash** for deep semantic resume-to-JD matching.
- **3-Node Agentic Pipeline**:
  - **Node 1 (Evaluator)**: Performs requirement extraction, missing skill identification, and calculates a multi-factor composite ATS score.
  - **Node 2 (Rewriter)**: Tailors bullet points without hallucinating candidate details, incorporating live candidate GitHub repository analysis for technical skill alignment.
  - **Node 3 (Generator)**: Produces job-specific cover letters, cold emails, and LinkedIn outreach messages while streaming newly formatted DOCX and PDF resume files back to cloud storage.
- **Targeted Interview Agent**: Dynamically generates tailored technical, behavioral, and gap-focused interview questions derived directly from the evaluation node's output.
- **Asynchronous Task Architecture**: Offloads heavy LLM and graph execution to a dedicated **Redis RQ** worker queue, returning results asynchronously via webhooks.
- **Stateless Authentication**: Validates Google OAuth ID tokens directly via `google-auth` for secure, stateless service-to-service communication.

---

## 🎯 Interview Agent Integration

Beyond static document generation, the system features an **Interview Agent** designed to prepare candidates for real-world screening calls:

- **Gap-Targeted Questions**: Analyzes the candidate's `truly_missing` and `partially_supported` skills to formulate technical probing questions standard interviewers will likely ask.
- **Behavioral & STAR Preparation**: Generates scenario-based questions built around the candidate's verified `experience_evidence` to help frame responses using the STAR method.
- **JD-Specific Technical Deep-Dives**: Extracts core architectural and tool-specific requirements from the Job Description to simulate role-specific technical rounds.
- **Constructive Feedback & Scoring**: Evaluates candidate mock responses, pinpointing weak explanations, technical inaccuracies, or areas needing stronger evidence.

---

## 🛠 Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Agentic Orchestration**: LangGraph, LangChain Core
- **Language Model**: Google GenAI SDK (`gemini-2.5-flash`)
- **NLP & Text Normalization**: spaCy, RapidFuzz
- **Background Processing**: Redis, Redis RQ
- **Cloud Storage & Auth**: Supabase Storage (`supabase-py`), Google OAuth (`google-auth`)
- **Document Exporting**: `python-docx`, ReportLab

---

## 📋 Active Development Roadmap

- [x] In-memory PDF/DOCX byte extraction and line normalization pipeline
- [x] Deterministic spaCy keyword engine + LLM evaluation node
- [x] 3-Node sequential LangGraph workflow execution engine
- [x] Background job processing queue with Redis RQ & webhooks
- [x] Direct binary document export (PDF/DOCX) to Supabase Storage
- [ ] Interview Agent workflow integration and interactive session state
- [ ] Comprehensive unit and integration test suite for agent state transitions
- [ ] API rate-limiting middleware and enhanced request validation
- [ ] Memory optimization for spaCy NLP pipelines under high concurrent load

---

## 📄 License

Internal Proprietary — All rights reserved.
