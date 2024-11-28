FROM python:3.11

WORKDIR /app

RUN pip install --upgrade pip

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY myapp.py .

CMD ["uvicorn", "myapp:app", "--host", "0.0.0.0", "--port", "8000"]