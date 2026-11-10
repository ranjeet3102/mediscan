# MediScan — Medical Report Simplifier 2.0

AI-powered medical report OCR, biomarker extraction, grounded RAG explanations, prescription parsing, longitudinal trend tracking, and Zero-PHI admin telemetry.

## Project Structure

- `backend/` — FastAPI REST API, OpenCV + Tesseract OCR pipeline, RAG medical glossary & chat (`pgvector` + Ollama / Groq), prescription & lab parsers, and Zero-PHI admin analytics.
- `frontend/` — Next.js 16 (App Router, TypeScript, Tailwind CSS) web portal for patients and administrators.
- `supabase/` — PostgreSQL + `pgvector` schema migrations, RLS policies, and storage setup.

## Getting Started

### 1. Backend
```bash
cd backend
cp .env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```
