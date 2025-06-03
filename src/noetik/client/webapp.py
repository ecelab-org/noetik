"""
Simple web UI for Noetik that communicates with the API backend.

This module provides a simple HTML interface that makes JavaScript
fetch calls to the /agent endpoint in api.py.
"""

from pathlib import Path

from fastapi import (
    FastAPI,
    Request,
)
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from noetik.common import (
    AnsiColors,
    colored_print,
)
from noetik.config import settings


def create_index_html(path: Path) -> bool:
    """Create the index.html file for the web interface"""
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(
                f"""\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Noetik</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }}
        .chat-container {{
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 10px;
            height: 400px;
            overflow-y: auto;
            margin-bottom: 15px;
            background-color: #f9f9f9;
        }}
        .message {{
            padding: 10px;
            margin: 10px 0;
            border-radius: 6px;
            max-width: 80%;
        }}
        .user-message {{
            background-color: #ddeeff;
            margin-left: auto;
        }}
        .assistant-message {{
            background-color: #eef9e6;
        }}
        .input-area {{
            display: flex;
        }}
        #message-input {{
            flex-grow: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-right: 10px;
        }}
        button {{
            padding: 10px 15px;
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }}
        button:hover {{
            background-color: #2980b9;
        }}
    </style>
</head>
<body>
    <h1>🔮 Noetik</h1>
    <div class="chat-container" id="chat-container"></div>
    <div class="input-area">
        <input type="text" id="message-input" placeholder="Type your message here...">
        <button id="send-button">Send</button>
    </div>

    <script>
        const API_URL = window.location.hostname === 'localhost'
        ? 'http://localhost:{settings.API_PORT}'  // Development
        : '';  // Production (same domain, different port)
        const chatContainer = document.getElementById('chat-container');
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');

        function addMessage(text, isUser) {{
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message');
            messageDiv.classList.add(isUser ? 'user-message' : 'assistant-message');
            messageDiv.textContent = text;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }}

        async function sendMessage() {{
            const message = messageInput.value.trim();
            if (!message) return;

            addMessage(message, true);
            messageInput.value = '';
            messageInput.disabled = true;
            sendButton.disabled = true;

            try {{
                const response = await fetch(`${{API_URL}}/agent`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{ message }}),
                }});

                if (response.ok) {{
                    const data = await response.json();
                    addMessage(data.reply, false);
                }} else {{
                    const errorData = await response.json();
                    addMessage(`Error: ${{errorData.detail || 'Something went wrong'}}`, false);
                }}
            }} catch (error) {{
                addMessage(`Error: ${{error.message}}`, false);
            }} finally {{
                messageInput.disabled = false;
                sendButton.disabled = false;
                messageInput.focus();
            }}
        }}

        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {{
            if (e.key === 'Enter') sendMessage();
        }});

        // Add welcome message
        addMessage("Welcome to Noetik! How can I help you today?", false);
    </script>
</body>
</html>
        """
            )
    except Exception as e:  # pylint: disable=broad-except
        colored_print(f"Error creating index.html: {e}", AnsiColors.RED)
        return False
    return True


# Create a FastAPI app for the web UI
webapp = FastAPI(
    title="Noetik Web UI", version="0.1.0", description="Noetik AI orchestrator web interface"
)

# Set up templates directory - assuming we'll create this structure
templates_dir = Path(settings.DATA_DIR) / "webui/templates"
templates_dir.mkdir(exist_ok=True, parents=True)
templates = Jinja2Templates(directory=str(templates_dir))

# Serve static files if we add CSS/JS later
static_dir = Path(settings.DATA_DIR) / "webui/static"
static_dir.mkdir(exist_ok=True, parents=True)
webapp.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Create the main HTML template if it doesn't exist
index_template = templates_dir / "index.html"
if not index_template.exists():
    create_index_html(path=index_template)


@webapp.get("/", response_class=HTMLResponse)
async def read_root(request: Request) -> HTMLResponse:
    """Serve the main web UI page."""
    return templates.TemplateResponse("index.html", {"request": request})


def run_webapp(
    host: str = "0.0.0.0", port: int = 8080, reload: bool = False, log_level: str | None = None
) -> None:
    """Run the web UI server."""
    import uvicorn  # pylint: disable=import-outside-toplevel

    if log_level is None:  # Use the default from settings if not provided
        log_level = settings.LOG_LEVEL

    colored_print(
        "Web UI is running at http://localhost:8080. Visit this URL in your browser.",
        AnsiColors.GREEN,
    )
    colored_print(
        "Press Ctrl+C to stop the server.",
        AnsiColors.YELLOW,
    )
    uvicorn.run(
        "noetik.client.webapp:webapp",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
    )


if __name__ == "__main__":
    run_webapp(reload=False)
    colored_print(
        "Web UI is running at http://localhost:8080. Visit this URL in your browser.",
        AnsiColors.GREEN,
    )
    colored_print(
        "Press Ctrl+C to stop the server.",
        AnsiColors.YELLOW,
    )
