from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import Response, JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

import auth, database, schema

router = APIRouter(tags=['User'])

@router.post('/user', response_model=str, status_code=status.HTTP_201_CREATED)
async def create_user(
	user: schema.user.UserCreate,
	db: database.DB = Depends(database.provide_db)
) -> Response:
	db_user = await db.query_item(database.models.User, username=user.username)
	if db_user:
		raise HTTPException(
			status_code=status.HTTP_409_CONFLICT,
			detail='Username already exists',
			headers={'WWW-Authenticate': 'Bearer'}
		)

	db_user = database.models.User(
		username=user.username,
		hashed_pw=auth.bcrypt_hash(user.password),
		is_admin=False
	)
	db.session.add(db_user)

	await db.session.commit()
	await db.session.refresh(db_user)

	return Response(db_user.uid, status_code=status.HTTP_201_CREATED)

@router.post('/token', response_model=schema.user.TokenAccess, status_code=status.HTTP_200_OK)
async def login_for_token(
	oauth2: OAuth2PasswordRequestForm = Depends(),
	db: database.DB = Depends(database.provide_db)
) -> Response:
	db_user = await db.query_item(database.models.User, username=oauth2.username)
	if db_user is None:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail='Could not validate credentials',
			headers={'WWW-Authenticate': 'Bearer'}
		)

	if not auth.bcrypt_verify(oauth2.password, db_user.hashed_pw):
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail='Could not validate credentials',
			headers={'WWW-Authenticate': 'Bearer'}
		)

	access_token = auth.create_jwt(
		db_user.username,
		expire_mins=60
	)

	json_res = {
		'access_token': access_token,
		'is_admin': db_user.is_admin
	}
	return JSONResponse(json_res, status_code=status.HTTP_200_OK)
