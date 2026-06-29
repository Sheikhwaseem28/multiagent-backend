# DeepScout Backend - Multi-Agent AI Research System

Welcome to the backend repository of **DeepScout**, an autonomous, multi-agent AI research platform. This backend acts as the intelligent orchestration engine that coordinates specialized AI agents to perform complex web research, deep reading, content synthesis, and peer review.

## 🚀 Key Features

- **Multi-Agent Orchestration**: Utilizes a highly specialized pipeline of AI agents working sequentially to mimic a human research workflow.
- **Real-Time Streaming API (SSE)**: Built on FastAPI to stream live updates (Agent starts, progress, logs) directly to the frontend interface.
- **Autonomous Web Search**: Integrates with the Tavily Search API for optimized, AI-driven internet searches.
- **Intelligent Web Scraping**: Asynchronously fetches and cleans HTML content from multiple URLs using BeautifulSoup4 and aiohttp.
- **Configurable Research Depths**: Supports dynamic research modes (Quick, Standard, Deep) dictating the breadth of search and strictness of the review process.

## ⚙️ Workflow & Architecture

The backend operates on a sequential pipeline architecture (`pipeline.py`), passing state and data between the following AI agents:

1. **Search Agent (`agents.py`)**: 
   Takes the user's topic and determines the best search queries. It uses the `Tavily` tool to fetch highly relevant web sources, URLs, and snippets.
2. **Reading Agent (`tools.py` & `agents.py`)**: 
   Iterates through the discovered URLs, asynchronously scrapes the raw HTML, parses out the noise (ads, navbars) using `BeautifulSoup4`, and extracts the core text.
3. **Writing Agent (`agents.py`)**: 
   Synthesizes the massive amount of scraped data into a highly structured, comprehensive Markdown report, complete with citations.
4. **Review Agent (`agents.py`)**: 
   Acts as a strict peer reviewer. It critiques the Writer's draft, evaluates factual accuracy, formats, and assigns a final quality score (out of 10).

## 🛠️ Technology Stack

- **Core Framework**: FastAPI, Uvicorn
- **AI Ecosystem**: LangChain, LangChain Core/Community, LangChain OpenAI
- **LLM Provider**: Google Gemini (gemini-2.5-flash)
- **Search Engine**: Tavily Search API
- **Web Scraping**: BeautifulSoup4, requests, lxml, aiohttp
- **Data Validation**: Pydantic
- **Environment Management**: python-dotenv

## 📦 Setup & Installation

### 1. Prerequisites
Ensure you have Python 3.9+ installed on your machine.

### 2. Clone and Install Dependencies
```bash
# Clone the repository and navigate to the backend folder
cd Multi-agent-backend

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install the required packages
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root of the backend directory and add your API keys:
```env
OPENAI_API_KEY="your_openai_api_key_here"
TAVILY_API_KEY="your_tavily_api_key_here"
```

## 🏃‍♂️ Running the Server

Start the FastAPI backend server using Uvicorn:

```bash
uvicorn app:app --reload --port 8000
```
The API will now be available at `http://localhost:8000`. 
To view the automatically generated API documentation (Swagger UI), visit `http://localhost:8000/docs`.

## 📡 API Endpoints
- `POST /research/stream`: Initiates the multi-agent pipeline and opens a Server-Sent Events (SSE) connection to stream real-time JSON logs and the final Markdown report back to the client.
