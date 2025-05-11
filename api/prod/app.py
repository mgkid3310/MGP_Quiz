from datetime import datetime, timezone

from fastapi import FastAPI, status
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import router

app = FastAPI()

app.add_middleware(
	CORSMiddleware,
	allow_origins=['*'],
	allow_credentials=True,
	allow_methods=['*'],
	allow_headers=['*']
)

@app.get('/', include_in_schema=False)
async def root() -> Response:
	json_res = {'message': f'Server is responsive at {datetime.now(timezone.utc)}'}
	return JSONResponse(json_res, status.HTTP_200_OK)

for rtr in router.routers:
	app.include_router(rtr)
