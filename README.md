# 🧠 QORA RESEARCH AI

The world's most advanced autonomous AI research intelligence platform. Built to automate 80% of a researcher's grunt work.

## 🌟 What it Does
- **Searches** ArXiv, Semantic Scholar, PubMed, and OpenAlex.
- **Reads** and extracts key findings, methods, and limitations from hundreds of papers.
- **Synthesizes** the research landscape to find critical gaps and generate novel hypotheses.
- **Visualizes** paper connections and methodologies in a 3D knowledge graph.
- **Writes** a comprehensive, publication-ready literature review in Markdown.

## 🚀 How to Run

1. Open the `backend/.env.example` file, add your API keys, and rename it to `.env`.
   - You **must** provide a valid `LLM_API_KEY` (OpenAI format, works with Groq, Together, etc.).
2. Double click `start.bat`. This will install dependencies and start the backend server on `http://localhost:8000`.
3. Open `frontend/index.html` in any modern web browser.
4. Type in a research topic and watch the magic happen!

## 🔧 Tech Stack
- **Backend:** FastAPI, Python, AsyncIO
- **AI Core:** LangChain concepts (custom multi-agent orchestrator), AsyncOpenAI
- **Frontend:** HTML5, Glassmorphism CSS, Vanilla JS, D3.js + ForceGraph (for 3D visualizer)
