# MeetLoop — Local Setup & Development Guide

Follow this step-by-step guide to run **MeetLoop** locally in under 10 minutes.

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+ & npm**
- **Swytchcode CLI** (`npm install -g @swytchcode/cli` or binary)
- **API Keys**:
  - OpenRouter API Key (or OpenAI / Anthropic)
  - Swytchcode API Key
  - Notion Workspace Access
  - Gmail Account (for manager digest testing)
  - Slack Workspace & Channel ID
  - (Optional) Google Cloud OAuth credentials for Google Meet transcript fetching

---

## 1. Clone the Repository

```bash
git clone https://github.com/yourusername/meetloop.git
cd meetloop
```

---

## 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On macOS / Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

Edit `backend/.env` with your actual credentials:
```ini
OPENROUTER_API_KEY=your_openrouter_key
OPENROUTER_MODEL=openrouter/free
SWYTCHCODE_API_KEY=your_swytchcode_key
NOTION_WORKSPACE_ID=your_notion_workspace_id
NOTION_HEALTH_REPORT_PARENT_PAGE_ID=your_notion_parent_page_id
GMAIL_TEST_ACCOUNT=your_manager_email@gmail.com
SLACK_WORKSPACE_ID=your_slack_workspace_id
SLACK_CHANNEL_ID=C0C4DT5SW5R
```

---

## 3. Swytchcode Policy & Integrations Initialization

```bash
# Initialize Swytchcode project
swy init

# Authenticate required destination integrations
swy auth notion
swy auth gmail
swy auth slack

# Validate policies
swy policy validate
```

---

## 4. (Optional) Google Meet Transcript Auth

If you want to fetch live Google Meet transcripts directly using meeting space codes (e.g. `abc-defg-hij`):

```bash
python tools/gmeet_auth.py
# Complete the one-time Google OAuth browser consent flow (saves token.json locally)
```
*(Note: If no Google Meet token is present, MeetLoop automatically uses its realistic mock conference walker).*

---

## 5. Start the FastAPI Backend

```bash
# Inside backend/ directory:
uvicorn api.main:app --reload --port 8000
```
- API Base URL: `http://localhost:8000`
- Interactive Swagger Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

---

## 6. Frontend Setup ("The Investigation Room")

Open a new terminal window:

```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```
- Frontend UI: `http://localhost:5173`

---

## 7. Verification & Smoke Test

1. Open `http://localhost:5173` in your browser.
2. Click **"Quick Sample Audit (PulseBoard)"** or **"Launch Investigation Studio"**.
3. Watch the **Orbital Stage Hub** light up as Swytchcode validates destination policies across Ingestion $\rightarrow$ Reasoning $\rightarrow$ Notion $\rightarrow$ Gmail $\rightarrow$ Slack.
4. Review the final **Investigation Room Verdict**, including workload breakdown and live artifact links.
