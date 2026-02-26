# Traction Backend

A platform that gives founders a web presence for their ideas before they build anything - shareable, discoverable, and credible. By allowing founders to easily structure their ideas, receive AI-generated feedback, and instantly produce an elegant web summary and pitch deck, Nebular Blazar replaces scattered PDFs and slides with a single, modern URL.

## Features

- **Ideation Assistant**: Chat with an AI that helps refine messy ideas into structured business models while offering honest readiness flags.
- **Dynamic Deck Generation**: AI automatically generates rich, interactive, full-screen HTML/CSS/JS pitch decks based on structured data.
- **Investor Summary**: Instantly highlights strengths, concerns, and key metrics in a simple view.
- **llm.txt Endpoints**: Provides a machine-readable startup spec, optimized for AI agents discovering projects.
- **Effortless Sharing**: Share one link that includes both the generated pitch deck and summary.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **ORM**: SQLModel / SQLAlchemy
- **Database Migrations**: Alembic
- **AI Models**: OpenAI API, Pydantic-AI
- **Authentication**: JWT, Google OAuth 2.0 Authlib
- **Templating**: Jinja2 (server-side rendered views)
- **Environment Management**: uv (Python package manager)

## Prerequisites

- Python 3.12+
- uv package manager
- Docker and Docker Compose (for running PostgreSQL locally)

## Getting Started

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd traction-backend
   ```

2. **Configure Environment Variables**
   Create or modify the `.env` file in the root directory to ensure all necessary keys are populated. Typical required values include database credentials, secret keys, Google API credentials, and your OpenAI API key.

3. **Start the Database**
   Using Docker Compose, you can quickly spin up a local PostgreSQL instance:
   ```bash
   docker-compose up -d
   ```

4. **Install Dependencies**
   Install the Python environment and dependencies using uv:
   ```bash
   uv sync
   ```

5. **Start the Development Server**
   Start the FastAPI development server with Uvicorn:
   ```bash
   cd backend
   uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   The backend will be available at http://localhost:8000.

## Project Structure

- `backend/app/`: Core FastAPI application logic (controllers, models, API routes, templates, etc.)
- `alembic/` (if configured): Database migrations
- `docker-compose.yml`: Local database orchestration
- `pyproject.toml` & `uv.lock`: Dependency definitions and locks

---

*Note: This backend also handles the frontend rendering using server-side Jinja2 templates for public views. Everything operates securely within the FastAPI structure without requiring a separate frontend deployment.*
