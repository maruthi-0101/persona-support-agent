# 🤖 Persona-Adaptive Customer Support Agent

An intelligent customer support agent that classifies user personas in real time and generates tailored responses using **Retrieval-Augmented Generation (RAG)** powered by **Google Gemini 2.5 Flash-Lite**, **ChromaDB**, and **LangChain**.

---

## 📋 Project Overview

Traditional customer support chatbots deliver one-size-fits-all responses regardless of who is asking. This project solves that problem by:

1. **Classifying the user's persona** — detecting whether the user is a *Technical Expert*, *Frustrated User*, or *Business Executive*.
2. **Retrieving relevant knowledge** — using vector similarity search over support documents stored in ChromaDB.
3. **Generating adaptive responses** — tailoring the tone, depth, and format of the answer to match the detected persona.
4. **Escalating when necessary** — automatically handing off to human agents for billing, legal, refund, or low-confidence scenarios.

---

## 🏗️ Architecture

```
User Query
    │
    ▼
┌──────────────────────┐
│  Persona Classifier   │  ← Gemini 2.5 Flash-Lite
│  (Technical Expert /  │
│   Frustrated User /   │
│   Business Executive) │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  ChromaDB Vector     │  ← text-embedding-004
│  Retrieval (Top-K)   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Escalation Check    │  ← Score < 0.45 or sensitive keywords
└──────────┬───────────┘
           │
     ┌─────┴─────┐
     │           │
     ▼           ▼
┌─────────┐ ┌──────────────────┐
│ Handoff │ │ Adaptive Response │
│ to Human│ │ Generator         │
└─────────┘ └──────────────────┘
```

---

## 📁 Project Structure

```
persona-support-agent/
│
├── data/                          # Support knowledge-base documents
│   ├── api_troubleshooting.md
│   ├── billing_policy.txt
│   ├── password_reset_guide.pdf
│   ├── refund_policy.txt
│   ├── api_authentication.md
│   ├── database_integration.md
│   ├── login_troubleshooting.txt
│   └── account_recovery.txt
│
├── src/                           # Core modules
│   ├── __init__.py
│   ├── config.py                  # Configuration and constants
│   ├── classifier.py              # Persona classification
│   ├── rag_pipeline.py            # Embedding + vector retrieval
│   ├── generator.py               # Adaptive response generation
│   ├── escalator.py               # Escalation logic
│   └── ingest_data.py             # Document ingestion pipeline
│
├── chroma_db/                     # Vector database (auto-generated)
├── app.py                         # Streamlit application entry point
├── requirements.txt               # Python dependencies
├── README.md                      # This file
├── .env                           # Environment variables (not committed)
└── .gitignore
```

---

## ⚙️ Installation

### Prerequisites

- Python 3.11 or higher
- A Google Gemini API key ([Get one here](https://aistudio.google.com/apikey))

### Steps

```bash
# 1. Clone the repository
git clone <repo-url>
cd persona-support-agent

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your API key
#    Edit the .env file and replace the placeholder:
echo "GEMINI_API_KEY=your_actual_key" > .env

# 5. Ingest the support documents into ChromaDB
python -m src.ingest_data

# 6. Run the application
streamlit run app.py
```

---

## 🚀 Running the App

```bash
# Start the Streamlit UI
streamlit run app.py

# Or ingest documents only
python -m src.ingest_data
```

The app will open at `http://localhost:8501` in your browser.

---

## 🔮 Future Improvements

- [ ] **Conversation memory** — multi-turn context tracking with session history
- [ ] **Streaming responses** — real-time token-by-token Gemini output in the UI
- [ ] **User feedback loop** — thumbs up/down to improve persona classification accuracy
- [ ] **Multi-language support** — detect and respond in the user's language
- [ ] **Admin dashboard** — analytics on persona distribution, escalation rates, and response quality
- [ ] **Webhook integration** — connect escalation handoffs to Slack, Jira, or Zendesk
- [ ] **Fine-tuned classification** — train a lightweight classifier on real support ticket data
- [ ] **Authentication** — user login and role-based access control
- [ ] **Caching layer** — cache frequent queries to reduce API costs and latency

---

## 📄 License

This project is for educational and demonstration purposes.

---

*Built with ❤️ using Google Gemini, ChromaDB, LangChain, and Streamlit.*
