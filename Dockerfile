FROM continuumio/miniconda3:latest as builder

ARG BUILDKIT_INLINE_CACHE=1
ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_DEFAULT_REGION=ap-northeast-3
ARG AWS_S3_BUCKET=repick-chromadb
WORKDIR /

# pip 설정
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DEFAULT_TIMEOUT=300
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONUNBUFFERED=1

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    cmake \
    curl \
    unzip \
    tar \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# 기본 의존성 먼저 설치 (순서 중요)
RUN pip install --no-cache-dir -U pip wheel setuptools

# 핵심 패키지 먼저 설치
RUN pip install --no-cache-dir \
    numpy==1.26.2 \
    pandas>=2.2.2 \
    sympy==1.13.3 \
    tenacity==8.3.0

# 나머지 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --no-deps

# 나머지 파일들 복사
COPY . .

# AWS CLI 설치 최적화
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-$(uname -m | sed 's/x86_64/x86_64/;s/aarch64/aarch64/').zip" -o "awscliv2.zip" \
    && unzip -q awscliv2.zip \
    && ./aws/install --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli --update \
    && rm -rf aws awscliv2.zip

# 필요한 파일들만 복사
COPY app ./app
COPY chatbot ./chatbot
COPY data/vectordb ./data/vectordb
COPY src ./src
COPY scripts ./scripts

# 시작 스크립트 생성
RUN echo '#!/bin/bash\n\
    aws s3 cp s3://${AWS_S3_BUCKET}/vectordb/vectordb.tar.gz /tmp/vectordb.tar.gz && \
    tar -xzf /tmp/vectordb.tar.gz -C /data/vectordb && \
    rm /tmp/vectordb.tar.gz && \
    python -m app.api.test_chatbot_api' > /app/start.sh && \
    chmod +x /app/start.sh

EXPOSE 8000

CMD ["uvicorn", "app.api.test_chatbot_api:app", "--host", "0.0.0.0", "--port", "8000"]