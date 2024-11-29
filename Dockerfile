FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry

WORKDIR /app

# pyproject.toml과 poetry.lock 파일을 먼저 복사
COPY pyproject.toml poetry.lock ./

# 의존성 설치
RUN poetry install --no-root --no-dev

COPY agents ./agents
COPY app ./app
COPY chatbot ./chatbot
COPY data/vectordb ./data/vectordb
COPY prompts ./prompts
COPY src ./src
COPY scripts ./scripts
COPY tools ./tools

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "app.api.chatbot_api:app", "--host", "0.0.0.0", "--port", "8000"]