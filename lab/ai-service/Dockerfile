FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LLM_PROVIDER=stub \
    STUB_SLOW_SCALE=1.0

COPY pyproject.toml requirements.txt README.md ./
COPY ai_service ./ai_service
COPY fixtures ./fixtures

RUN pip install --no-cache-dir -e .

EXPOSE 8000

CMD ["uvicorn", "ai_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
