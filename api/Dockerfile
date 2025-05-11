FROM python:3.12-slim

COPY prod /app
WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
