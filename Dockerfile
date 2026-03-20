FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY packages/rae-agentic-memory/requirements-dev.txt .
RUN pip install --no-cache-dir fastapi uvicorn httpx structlog
COPY . .
EXPOSE 8009
CMD ["python", "main.py"]
