from sqlalchemy.ext.asyncio import create_async_engine

from . import _config as cfg

def create_engine():
	return create_async_engine(cfg.PG_URL, pool_recycle=3600, pool_pre_ping=True)

default_engine = create_engine()
