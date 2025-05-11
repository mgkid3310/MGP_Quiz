FROM python:3.12-slim

COPY prod /app
WORKDIR /app

RUN apt-get update && \
	apt-get install -y --no-install-recommends \
		curl && \
	pip install --upgrade pip && \
	pip install -r requirements.txt && \
	pip cache purge && \
	apt-get clean && \
	rm -rf /var/lib/apt/lists/*

EXPOSE 8000
CMD ["python", "main.py"]
