FROM python:3.12-slim

RUN pip install poetry

COPY prod /app
WORKDIR /app

RUN poetry config virtualenvs.create false && \
	poetry install --no-interaction --no-ansi --no-root

CMD ["poetry", "run", "python", "main.py"]
