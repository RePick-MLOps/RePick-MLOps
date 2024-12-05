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
    python3-dev

# AWS CLI 설치를 별도의 레이어로 분리
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-$(uname -m | sed 's/x86_64/x86_64/;s/aarch64/aarch64/').zip" -o "awscliv2.zip" \
    && unzip -q awscliv2.zip \
    && ./aws/install --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli --update \
    && rm -rf aws awscliv2.zip \
    && aws --version \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# pip로 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir chromadb==0.4.22 \
    && pip install --no-cache-dir -r requirements.txt

# 필요한 파일들 복사
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
