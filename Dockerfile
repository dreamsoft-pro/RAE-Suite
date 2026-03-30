FROM python:3.14-rc-slim
WORKDIR /app
COPY . .
# Instalacja rae-core jako pakietu lokalnego
RUN pip install fastapi uvicorn httpx pydantic pyyaml &&     pip install -e packages/rae-core
ENV PYTHONPATH=/app/src
CMD ["uvicorn", "rae_suite.main:app", "--host", "0.0.0.0", "--port", "8009"]
