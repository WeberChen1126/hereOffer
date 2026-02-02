FROM python:3.11-slim-bookworm

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# 可选：如果你在某些环境 cryptography 需要 openssl 运行库，装这个更稳（很小）
RUN apt-get update -o Acquire::Retries=5 -o Acquire::http::Timeout="30" \
 && apt-get install -y --no-install-recommends \
    ca-certificates \
    openssl \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]