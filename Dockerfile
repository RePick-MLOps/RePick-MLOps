FROM python:3.7.5

WORKDIR /app

RUN pip install --upgrade pip

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY chatbot_api ./chatbot_api

CMD ["uvicorn", "chatbot_api.app:app", "--host", "0.0.0.0", "--port", "8000"]