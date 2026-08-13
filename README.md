# ⚔️ Warhammer 40k & 30k Book Concierge

> **An AI-powered conversational concierge for Black Library literature, Horus Heresy reading roadmaps, reading progress tracking, custom cover art, and cinematic video generation.**

<div align="center">

[![Build with Gemini](https://img.shields.io/badge/Build%20with%20Gemini-Track%203-4285F4?logo=google&logoColor=white)](https://antigravity.google)
[![Google Cloud](https://img.shields.io/badge/Google%20Cloud-Agent%20Platform-4285F4?logo=googlecloud&logoColor=white)](https://cloud.google.com/vertex-ai)
[![ADK Framework](https://img.shields.io/badge/Built%20with-ADK%20%2B%20agents--cli-34A853)](https://google.github.io/adk-docs/)
[![A2UI Enabled](https://img.shields.io/badge/UI-A2UI%20Cards-EA4335)](https://adk.dev/integrations/a2ui/)

</div>

---

## 📖 Overview

Navigating the vast universe of Warhammer 40,000 and the 54+ volume Horus Heresy (30,000) series can be overwhelming for both newcomers and seasoned Warhammer veterans.

The **Warhammer 40k & 30k Book Concierge** is an agentic AI assistant designed to solve this problem. Built on Google's Agent Development Kit (ADK) and deployed to Vertex AI Agent Platform, it provides grounded literature recommendations, tracks reading history in real time, generates custom cartoon cover art and cinematic videos, and presents rich interactive cards.

<div align="center">

![Warhammer 40k & 30k Book Concierge Demo](assets/demo.gif)

</div>

---

## ✨ Key Features

- 📖 **Tailored Book & Audiobook Recommendations**: Get personalized novel and audiobook suggestions based on your favorite Space Marine Legions, xenos factions, or narrative interests.
- 🗺️ **Horus Heresy Chronological Reading Paths**: Access curated, step-by-step reading roadmaps for the 30k series tailored specifically to factions like Alpha Legion, Thousand Sons, Space Wolves, and Ultramarines.
- 💾 **Firestore Reading Activity Tracker**: Record finished physical books and audiobooks into a live Google Cloud Firestore database with user ratings and completion stats.
- 🔍 **Grounded Black Library Lore (RAG)**: Perform semantic searches over official Black Library reference guides and plot passages using Vertex AI RAG Engine.
- 🧠 **Cross-Session Memory Bank**: Automatically persist user preferences, favorite Legions, and reading progress across chat sessions using Vertex AI Memory Bank.
- 🎨 **Comic-Style Cover Art Generation**: Generate custom cartoon / comic-book style cover illustrations on demand powered by Google's `gemini-3.1-flash-lite-image`.
- 🎬 **Cinematic Video Generation**: Generate short action videos for Warhammer characters and scenes using Google's Omni model (`gemini-omni-flash-preview`).
- 🎴 **Agent-First A2UI Cards**: Render rich, structured cards directly in the chat UI for book recommendations and reading statistics.
- 🌐 **Imperial Dark Mode Frontend**: Fully customized dark mode web interface with Imperial Gold accents, online status indicators, and clickable prompt chips.

---

## ☁️ Google Cloud & AI Stack

This project leverages a comprehensive suite of Google Cloud and Gemini AI technologies:

| Google Cloud Tool / Service | Purpose & Usage in Agent |
|---|---|
| **[Vertex AI Agent Platform](https://cloud.google.com/vertex-ai)** | Cloud runtime hosting for the ADK reasoning engine and tools. |
| **[Vertex AI Memory Bank](https://cloud.google.com/vertex-ai)** | Persistent long-term memory store for user preferences and history. |
| **[Cloud Firestore](https://cloud.google.com/firestore)** | Real-time NoSQL database storing the live book catalog and reading activity. |
| **[Cloud Storage (GCS)](https://cloud.google.com/storage)** | Public object storage for generated cover art images and MP4 video assets. |
| **[Vertex AI RAG Engine](https://cloud.google.com/vertex-ai)** | Vector retrieval corpus over Black Library lore reference documents. |
| **[Gemini Image Generation](https://cloud.google.com/vertex-ai)** | Image generation tool using `gemini-3.1-flash-lite-image` (Nano Banana 2 Lite). |
| **[Google Omni Model](https://cloud.google.com/vertex-ai)** | Multimodal video generation tool using `gemini-omni-flash-preview`. |
| **[A2UI Protocol](https://adk.dev/integrations/a2ui/)** | Agent-to-User Interface JSON card schema and renderer. |
| **[Google Cloud Run](https://cloud.google.com/run)** | Containerized deployment for the FastAPI proxy and dark mode chat UI. |

---

## 📂 Project Architecture

```text
warhammer-book-concierge/
├── app/
│   ├── agent.py               # Core ADK agent logic, system prompt, and tools
│   ├── a2ui_utils.py          # A2UI callback transformer and JSON schema configuration
│   └── fast_api_app.py        # FastAPI server backend
├── frontend/
│   ├── main.py                # FastAPI proxy connecting browser to deployed agent engine
│   └── static/
│       └── index.html         # Imperial Dark Mode chat interface with A2UI renderer
├── assets/
│   └── demo.gif               # Optimized looping demo animation
├── agents-cli-manifest.yaml   # Deployment manifest configuration
├── pyproject.toml             # Python dependencies (managed via uv)
└── README.md                  # Project documentation
```

---

## 🛠️ Local Development & Quick Start

### 1. Install Dependencies
Ensure you have `uv` and `agents-cli` installed, then run:

```bash
uv sync
```

### 2. Test in Local Playground

```bash
uv run agents-cli playground
```

### 3. Run the Frontend Locally

```bash
cd frontend
AGENT_ENGINE_RESOURCE_NAME="projects/<project-id>/locations/<region>/reasoningEngines/<id>" \
AGENT_DIRECTORY="app" \
PORT=8080 \
uv run python main.py
```

Open `http://localhost:8080` in your browser to interact with the concierge.

---

## 🚀 Deployment

Deploy the agent engine to Vertex AI Agent Platform:

```bash
agents-cli deploy --project <PROJECT_ID> --region us-east1
```

Deploy the chat frontend proxy to Cloud Run:

```bash
gcloud run deploy warhammer-book-concierge-frontend \
  --source ./frontend \
  --region us-east1 \
  --allow-unauthenticated \
  --set-env-vars AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_ID>/locations/us-east1/reasoningEngines/<ENGINE_ID>",AGENT_DIRECTORY="app"
```

---

## 📄 License

This project was built during Track 3 of the **Build with Gemini** workshop for demonstration purposes.
