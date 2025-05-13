FROM python:3.12-slim

RUN pip install poetry

RUN apt-get update && \
	apt-get install -y --no-install-recommends \
		curl && \
	apt-get clean && \
	rm -rf /var/lib/apt/lists/*

COPY prod /app
WORKDIR /app

RUN poetry config virtualenvs.create false && \
	poetry install --no-interaction --no-ansi --no-root

EXPOSE 8000
CMD ["poetry", "run", "python", "main.py"]
