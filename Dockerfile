# Miniconda 기반 이미지 사용
FROM continuumio/miniconda3:latest

WORKDIR /app

COPY environment.yml .

# Conda 환경 생성 및 의존성 설치
RUN conda env create -f environment.yml && \
    conda clean -a && \
    echo "source activate my_env" > ~/.bashrc

ENV PATH /opt/conda/envs/my_env/bin:$PATH

COPY agents ./agents
COPY app ./app
COPY chatbot ./chatbot
COPY data/vectordb ./data/vectordb
COPY prompts ./prompts
COPY src ./src
COPY scripts ./scripts
COPY tools ./tools

EXPOSE 8000

CMD ["uvicorn", "app.api.test_chatbot_api:app", "--host", "0.0.0.0", "--port", "8000"]
