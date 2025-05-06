FROM python:3.11-slim as base

# Install build dependencies
RUN apt-get update && apt-get upgrade && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry

# Set workdir and copy project files
WORKDIR /app
COPY pyproject.toml poetry.lock* README.md ./

# Install runtime dependencies
RUN --mount=type=bind,source=.,target=/app \
    poetry config virtualenvs.create false \
    && poetry install --no-interaction

EXPOSE 8000
CMD ["python", "-m", "noetik.main"]
