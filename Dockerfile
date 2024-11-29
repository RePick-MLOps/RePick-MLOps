FROM python:3.11 AS builder

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

FROM python:3.11

WORKDIR /app

COPY --from=builder /app /app
COPY app/ .

ENV OPENAI_API_KEY=$OPENAI_API_KEY

CMD ["uvicorn", "api.chatbot_api:app", "--host", "0.0.0.0", "--port", "8000"]