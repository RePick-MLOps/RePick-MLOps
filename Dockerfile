FROM continuumio/miniconda3:latest

WORKDIR /app

# 필요한 빌드 도구들을 먼저 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    cmake \
    curl \
    unzip \
    tar \
    && curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" \
    && unzip awscliv2.zip \
    && ./aws/install \
    && rm -rf aws awscliv2.zip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# pip로 의존성 설치
RUN pip install --no-cache-dir chromadb==0.4.22 \
    && pip install --no-cache-dir -r requirements.txt

COPY agents ./agents
COPY app ./app
COPY chatbot ./chatbot
COPY data/vectordb ./data/vectordb
COPY prompts ./prompts
COPY src ./src
COPY scripts ./scripts
COPY tools ./tools

# S3에서 ChromaDB 데이터를 다운로드하는 스크립트 생성
RUN echo '#!/bin/bash\n\
    aws s3 cp s3://${AWS_S3_BUCKET}/vectordb/vectordb.tar.gz /tmp/vectordb.tar.gz && \
    tar -xzf /tmp/vectordb.tar.gz -C /app/data/vectordb && \
    rm /tmp/vectordb.tar.gz && \
    python -m app.api.test_chatbot_api' > /app/start.sh && \
    chmod +x /app/start.sh

EXPOSE 8000

CMD ["uvicorn", "app.api.test_chatbot_api:app", "--host", "0.0.0.0", "--port", "8000"]
