import os

PG_USER = os.getenv('POSTGRES_USER')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD')
PG_DATABASE = os.getenv('POSTGRES_DB')

PG_URL = f'postgresql+asyncpg://{PG_USER}:{PG_PASSWORD}@database:5432/{PG_DATABASE}'
