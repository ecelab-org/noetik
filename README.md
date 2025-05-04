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

---

## 📁 Project Structure

```
noetik/                               # Root project directory
├── src/                              # Source code root
│   └── noetik/                       # Main package directory
│       ├── agent/                    # Agent orchestration and reasoning
│       │   ├── __init__.py            # Package initializer for agent module
│       │   ├── agent_loop.py          # Main orchestration loop
│       │   ├── planner_interface.py   # Interface between loop and LLM
│       │   ├── schema.py              # Tool call + planner schemas
│       │   └── tool_executor.py       # Tool dispatch logic
│       │
│       ├── examples/                 # Example implementations and demos
│       │   ├── __init__.py            # Package initializer for examples
│       │   └── run_demo_agent.py      # Quickstart agent demo
│       │
│       ├── memory/                   # Memory and storage capabilities
│       │   ├── __init__.py            # Package initializer for memory module
│       │   ├── memory_store.py        # JSON/SQLite local memory
│       │   └── vector_memory.py       # Embedding and vector DB interface
│       │
│       ├── tools/                    # Tool definitions and implementations
│       │   ├── __init__.py            # Tool registry + decorators
│       │   ├── code_tools.py          # Code execution
│       │   ├── shell_tools.py         # Shell command tools
│       │   └── web_tools.py           # Search, summarization
│       │
│       ├── web/                      # Web API and server components
│       │   ├── __init__.py            # Package initializer for web module
│       │   └── api.py                 # FastAPI implementation for HTTP endpoints
│       │
│       ├── llm/                      # Language model integration
│       │   ├── __init__.py            # Package initializer for LLM module
│       │   ├── model_loader.py        # Adapter to vLLM, OpenAI, Anthropic, etc.
│       │   ├── planner.py             # LLM planning logic
│       │   └── responder.py           # User-facing message generation
│       │
│       ├── __init__.py                # Package initializer for noetik
│       ├── config.py                  # Centralized settings and environment vars
│       └── main.py                    # Entry point: CLI or API
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
  - LLM libraries (depending on provider choice)
  - Vector database clients
  - Web frameworks
  - Utility libraries

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

# For help with options
$ ./start.sh --help
```

The `start.sh` script will:
- Check for Docker and Docker Compose
- Create a `.env` file from the template if needed
- Build the container only when dependencies change (faster restarts)
- Start the container in the selected mode (api or cli)

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
- `PORT`: The port to expose the API (default: 8000)
- `LLM_PROVIDER`: Your LLM provider (openai, anthropic, local)
- `*_API_KEY`: API keys for various services

---

## 🖥️ Usage

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
you> Tell me about the weather
noetik> What location would you like weather information for?
you> New York
noetik> (fetching weather data...)
```

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

Send a message:
```bash
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the capital of France?"}'
```

---

## 🧠 Why "Noetik"?

From the Greek *noetikos* (νοητικός), meaning "of the mind or intellect."
Noetik is about reasoning. Not just answering questions, but understanding context, reflecting, and acting with memory and tools.

---

## ❓ Troubleshooting

- **Port already in use**: Change the PORT value in your .env file
- **Connection refused**: Ensure the container is running properly with `docker ps`
- **Environment variables not working**: Check that your .env file is in the project root

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
