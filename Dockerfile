FROM python:3.14-rc-slim
WORKDIR /app
COPY . .
RUN pip install fastapi uvicorn httpx pydantic pyyaml && \
    pip install -e packages/rae-core
ENV PYTHONPATH=/app:/app/packages/rae-core/src
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8009"]
