# NOETIK

**Modular AI Orchestration System**

---

> "Intelligence isn't magic. It's orchestration."

**Noetik** is a modular, extensible AI orchestration framework designed to bring together reasoning, memory, and tool-use into a single cohesive loop. It coordinates open-source LLMs, vector memory, shell tools, APIs, and user-defined functions to enable intelligent, autonomous action.

---

## 🔍 Features

- **Planner-powered orchestration**: Use any LLM (local or remote) to decide what actions to take.
- **Tool registry**: Define modular tools in Python; auto-discover and invoke them via the planner.
- **Memory integration**: Chroma/Weaviate/JSON-based memory for stateful reasoning.
- **Multi-turn agent loop**: Reflect, act, and reason across multiple steps.
- **Pluggable components**: Swap planners, tools, memory, or executors with minimal friction.
- **Client-server architecture**: Core logic in API with multiple frontends (CLI, Web UI).

---

## 📁 Project Structure

```
noetik/                               # Root project directory
├── src/                              # Source code root
│   └── noetik/                       # Main package directory
│       ├── api/                      # Core API backend
│       │   ├── __init__.py            # Package initializer
│       │   ├── app.py                 # FastAPI implementation and business logic
│       │   └── models.py              # Pydantic models for API requests/responses
│       │
│       ├── client/                   # Frontend clients
│       │   ├── __init__.py            # Package initializer
│       │   ├── cli.py                 # Command-line interface client
│       │   └── webapp.py              # Web UI client interface
│       │
│       ├── core/                     # Core agent components
│       │   ├── __init__.py            # Package initializer
│       │   ├── planner.py             # Interface with LLMs for planning
│       │   ├── schema.py              # Tool call + planner schemas
│       │   └── tool_executor.py       # Tool dispatch logic
│       │
│       ├── memory/                   # Memory and storage capabilities
│       │   ├── __init__.py            # Package initializer
│       │   ├── memory_store.py        # Saving and retrieving agent turns
│       │   └── vector_memory.py       # Embedding and vector DB interface
│       │
│       ├── tools/                    # Tool definitions and implementations
│       │   ├── __init__.py            # Tool registry + decorators
│       │   └── [additional tool files] # Various tool implementations
│       │
│       ├── __init__.py                # Package initializer for noetik
│       ├── common.py                  # Common utilities (ANSI colors, etc.)
│       ├── config.py                  # Centralized settings and environment vars
│       └── main.py                    # Entry point: CLI, API, or Web UI
│
├── tests/                            # Test suite
│   └── test_tool_executor.py          # Tests for tool execution system
│
├── .dockerignore                      # Files to ignore during Docker build
├── .env.template                      # Template for environment configuration
├── .gitignore                         # Git ignore patterns
├── docker-compose.yml                 # Docker Compose configuration
├── Dockerfile                         # Container definition
├── LICENSE                            # Project license
├── pyproject.toml                     # Python package configuration
├── README.md                          # This documentation
└── start.sh                           # Convenience script for Docker startup
```

---

## 📋 Requirements

### Docker Setup (Recommended)
- Docker Engine (20.10.0+)
- Docker Compose (2.0.0+)

### Manual Setup
- Python 3.11+
- pip package manager
- Required Python packages (installed via Poetry):
  - LLM libraries (OpenAI, Anthropic)
  - Vector database clients (ChromaDB)
  - Web frameworks (FastAPI, Uvicorn)
  - Utility libraries (Pydantic, HTTPX)

The Docker setup automatically configures the correct Python version and all dependencies in an isolated environment, which is why it's the recommended approach.

---

## 🚀 Quickstart

### Option 1: Using Docker (Recommended)

```bash
# Clone the repository
$ git clone https://github.com/ecelab-org/noetik.git
$ cd noetik

# Start the container (automatically builds and configures) and run in API mode (default)
$ ./start.sh

# Or run in CLI mode
$ ./start.sh --mode cli

# Or run in Web UI mode
$ ./start.sh --mode web

# For help with options
$ ./start.sh --help
```

The `start.sh` script will:
- Check for Docker and Docker Compose
- Create a `.env` file from the template if needed
- Build the container only when dependencies change (faster restarts)
- Start the container in the selected mode (api, cli, or web)

### Option 2: Manual Setup

```bash
# Clone the repository
$ git clone https://github.com/ecelab-org/noetik.git
$ cd noetik

# Install using Poetry
$ pip install poetry
$ poetry install

# Run the application
$ poetry run python -m noetik.main
```

### Environment Configuration

Noetik uses environment variables for configuration. Copy `.env.template` to `.env` and modify as needed:

```bash
cp .env.template .env
# Edit .env with your preferred settings and API keys
```

Key variables include:
- `API_PORT`: The port for the API backend (default: 8000)
- `WEBUI_PORT`: The port for the Web UI (default: 8080)
- `PLANNER`: Your LLM provider (openai, anthropic, tgi)
- `*_API_KEY`: API keys for various services

---

## 🖥️ Usage

Noetik follows a client-server architecture, where the API serves as the backend and both CLI and Web UI are clients. All core functionality is implemented in the API, ensuring consistent behavior across interfaces.

### CLI Mode

**Using Docker:**
```bash
./start.sh --mode cli
```

**Using Python directly:**
```bash
python -m noetik.main --mode cli
```

**Example interaction:**
```
🔮  Noetik shell - type 'exit' to quit.

🧑 You: Tell me about the weather
🤖 What location would you like weather information for?

🧑 You: New York
🤖 (fetching weather data...)
```

### Web UI Mode

**Using Docker:**
```bash
./start.sh --mode web
```

**Using Python directly:**
```bash
python -m noetik.main --mode web
```

This starts a web interface accessible at http://localhost:8080 (or the port specified in your .env file).

### API Mode

**Using Docker:**
```bash
./start.sh --mode api
```

**Using Python directly:**
```bash
python -m noetik.main --mode api
```

**Example API requests:**

Health check:
```bash
curl http://localhost:8000/health
```

Create a session:
```bash
curl -X POST http://localhost:8000/sessions
```

Send a message:
```bash
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the capital of France?", "session_id": "your-session-id"}'
```

---

## 🧠 Why "Noetik"?

From the Greek *noetikos* (νοητικός), meaning "of the mind or intellect."
Noetik is about reasoning. Not just answering questions, but understanding context, reflecting, and acting with memory and tools.

---

## ❓ Troubleshooting

- **Port already in use**: Change the API_PORT or WEBUI_PORT values in your .env file
- **Connection refused**: Ensure the container is running properly with `docker ps`
- **Environment variables not working**: Check that your .env file is in the project root
- **API not responding**: When using CLI or Web UI, ensure the API has fully started

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## ✨ Taglines

- *"Orchestrating intelligence, one decision at a time."*
- *"Plug in tools. Wire up models. Let Noetik think."*
- *"Cognitive infrastructure for autonomous AI agents."*

---

## 🧩 Contributing

Pull requests welcome! Especially for new tools, planner wrappers, and memory backends.

- Run `black` and `ruff` before submitting.
- Include docstrings and type hints.
- Add your tool to `tools/__init__.py` with `@register_tool()`.

---

Built with clarity, curiosity, and composability. ✨
