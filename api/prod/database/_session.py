from datetime import datetime, timezone, timedelta
from hashlib import sha256
from typing import TypeVar, cast, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, InstrumentedAttribute, selectinload
from sqlalchemy.sql import select

from ._engine import create_engine, default_engine

MODEL = TypeVar('MODEL', bound=DeclarativeBase)
INST_ATTR = InstrumentedAttribute | list[InstrumentedAttribute]

def _chain_opt(chain: INST_ATTR):
	if isinstance(chain, list):
		opt = selectinload(chain[0])
		for attr in chain[1:]:
			opt = opt.selectinload(attr)
	else:
		opt = selectinload(chain)

	return opt

def _build_stmt(model: type[MODEL], joined: list[INST_ATTR] | None = None, **kwargs):
	stmt = select(model)

	for k, v in kwargs.items():
		attr = getattr(model, k)
		if not isinstance(attr, InstrumentedAttribute):
			raise AttributeError(f'{model.__name__} has no attribute {k}')

		if isinstance(v, list):
			stmt = stmt.where(attr.in_(v))
		else:
			stmt = stmt.where(attr == v)

	for chain in joined or []:
		opt = _chain_opt(chain)
		stmt = stmt.options(opt)

	return stmt

class Cache():
	def __init__(self, data, TTL: timedelta):
		self.data = data
		self.created = datetime.now(timezone.utc)
		self.TTL = TTL

	def expired(self) -> bool:
		return datetime.now(timezone.utc) > self.created + self.TTL

	async def merged(self, session: AsyncSession) -> Any:
		if isinstance(self.data, list):
			return [await session.merge(item) for item in self.data]
		else:
			return await session.merge(self.data)

class DB():
	config: dict = {
		'TTL': timedelta(minutes=15)
	}
	item_cache: dict[str, Cache] = {}
	list_cache: dict[str, Cache] = {}

	def __init__(self, new_engine: bool = False):
		self._dispose_after_use = new_engine
		self.engine = create_engine() if new_engine else default_engine

	async def __aenter__(self):
		self.session = AsyncSession(self.engine, autoflush=False, expire_on_commit=False)

		return self

	async def __aexit__(self, exc_type, exc_val, exc_tb):
		if exc_type:
			await self.session.rollback()
		else:
			await self.session.commit()

		await self.session.close()

		if self._dispose_after_use:
			await self.engine.dispose()

	async def query_item(
		self,
		model: type[MODEL],
		joined: list[INST_ATTR] | None = None,
		cache: bool = False,
		**kwargs
	) -> MODEL | None:
		""""
		Queries a single item from the database.

		:param model: The model to query. Must be a subclass of DeclarativeBase.
		:param joined: A list of InstrumentedAttribute objects to join. Use list for nested joins.
		:param kwargs: The query parameters. When the value is a list, the query will use the IN operator.
		:return: The queried item.
		"""

		stmt = _build_stmt(model, joined, **kwargs)

		stmt_hash = sha256(str(stmt).encode()).hexdigest()
		if cache and stmt_hash in self.item_cache:
			if not self.item_cache[stmt_hash].expired():
				return await self.item_cache[stmt_hash].merged(self.session)
			else:
				del self.item_cache[stmt_hash]

		result = await self.session.execute(stmt)
		result = result.scalars().first()

		if cache and result:
			self.item_cache[stmt_hash] = Cache(result, self.config['TTL'])

		return result

	async def query_list(
		self,
		model: type[MODEL],
		joined: list[INST_ATTR] | None = None,
		offset: int = 0,
		limit: int = -1,
		cache: bool = False,
		**kwargs
	) -> list[MODEL]:
		"""
		Queries a list of items from the database.

		:param model: The model to query. Must be a subclass of DeclarativeBase.
		:param joined: A list of InstrumentedAttribute objects to join. Use list for nested joins.
		:param offset: The offset to start the query from.
		:param limit: The maximum number of items to return. -1 for no limit.
		:param kwargs: The query parameters. When the value is a list, the query will use the IN operator.
		:return: The queried list of items.
		"""

		stmt = _build_stmt(model, joined, **kwargs)

		if limit > 0:
			stmt = stmt.limit(limit).offset(offset)

		stmt_hash = sha256(str(stmt).encode()).hexdigest()
		if cache and stmt_hash in self.list_cache:
			if not self.list_cache[stmt_hash].expired():
				return await self.list_cache[stmt_hash].merged(self.session)
			else:
				del self.list_cache[stmt_hash]

		result = await self.session.execute(stmt)
		result = result.scalars().all()

		if cache and result:
			self.list_cache[stmt_hash] = Cache(result, self.config['TTL'])

		return cast(list[MODEL], result)

async def provide_db():
	async with DB() as db:
		yield db
