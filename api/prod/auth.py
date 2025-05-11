from datetime import datetime, timezone, timedelta
import re

from fastapi import HTTPException, status, Path, Query
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError
import bcrypt

import config
import database

oauth2 = OAuth2PasswordBearer(tokenUrl='token')

def bcrypt_hash(password: str) -> str:
	pwd_bytes = password.encode('utf-8')
	hash_bytes = bcrypt.hashpw(password=pwd_bytes, salt=bcrypt.gensalt())

	return hash_bytes.decode('utf-8')

def bcrypt_verify(password: str, hashed: str) -> bool:
	password_enc = password.encode('utf-8')
	hashed_enc = hashed.encode('utf-8')

	return bcrypt.checkpw(password=password_enc, hashed_password=hashed_enc)

def create_jwt(username: str, expire_mins: int = 30) -> str:
	assert config.jwt_secret_key and config.jwt_algorithm

	expire = datetime.now(timezone.utc) + timedelta(minutes=expire_mins)
	payload = {
		'sub': username,
		'exp': expire
	}

	encoded_jwt = jwt.encode(payload, config.jwt_secret_key, algorithm=config.jwt_algorithm)
	return encoded_jwt

def decode_jwt(token: str) -> str:
	assert config.jwt_secret_key and config.jwt_algorithm

	try:
		if not token:
			raise JWTError('Empty token')

		payload = jwt.decode(token, config.jwt_secret_key, algorithms=[config.jwt_algorithm])

		username = payload.get('sub')
		if username is None:
			raise JWTError('Invalid username in token')

		return username

	except ExpiredSignatureError:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail='Token has expired',
			headers={'WWW-Authenticate': 'Bearer'}
		)

	except JWTError:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail='Could not validate token',
			headers={'WWW-Authenticate': 'Bearer'}
		)

async def jwt2user(token: str, admin: bool = False) -> database.models.User:
	username = decode_jwt(token)

	async with database.DB() as db:
		db_user = await db.query_item(
			database.models.User,
			username=username
		)

	if not db_user:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail='User not found',
			headers={'WWW-Authenticate': 'Bearer'}
		)

	if admin and not db_user.is_admin:
		raise HTTPException(
			status_code=status.HTTP_403_FORBIDDEN,
			detail='Admin access required',
			headers={'WWW-Authenticate': 'Bearer'}
		)

	return db_user

def check_sanity(target: str, path_op: bool = True, str_op: bool = True, comment_op: bool = True) -> bool:
	path_op_pattern = re.compile(r'\.\.|/|\\')			# check: .., /, \
	str_op_pattern = re.compile(r'["\']')				# check: ", '
	comment_op_pattern = re.compile(r'#|--|/\*|\*/')	# check: #, --, /*, */

	if path_op and path_op_pattern.search(target):
		return False

	if str_op and str_op_pattern.search(target):
		return False

	if comment_op and comment_op_pattern.search(target):
		return False

	return True

def path(path: str):
	def _check(param: str) -> str:
		if param is not None and not check_sanity(param):
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail='Invalid path parameter'
			)
		return param

	def _wrapper(param: str = Path(alias=path)) -> str:
		return _check(param)

	return _wrapper

def query(query: str, default = None):
	def _check(param: str) -> str:
		if param is not None and not check_sanity(param):
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail='Invalid query parameter'
			)
		return param

	def _wrapper(param: str = Query(default, alias=query)) -> str:
		return _check(param)

	return _wrapper
