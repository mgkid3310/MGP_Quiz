from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import Response, JSONResponse

import auth, database, schema

router = APIRouter(tags=['Quiz - Student'])

@router.get('/student/quiz', response_model=dict[str, schema.quiz.Quiz])
async def get_assigned_quizzes(
	token: str = Depends(auth.oauth2),
	db: database.DB = Depends(database.provide_db)
) -> Response:
	db_user = await auth.jwt2user(db, token)

	await db.session.run_sync(lambda s: s.refresh(db_user, ['assignments']))

	return JSONResponse(
		{a.quiz.uid: a.quiz.dump() for a in db_user.assignments},
		status_code=status.HTTP_200_OK
	)

@router.get('/student/quiz/{uid}', response_model=schema.quiz.QuizDetail)
async def get_quiz_detail(
	uid: str = Depends(auth.path('uid')),
	page: int = Query(1, ge=1),
	token: str = Depends(auth.oauth2),
	db: database.DB = Depends(database.provide_db)
) -> Response:
	db_user = await auth.jwt2user(db, token)

	db_assignment = await db.query_item(
		database.models.Assignment,
		user_uid=db_user.uid,
		quiz_uid=uid
	)

	if not db_assignment:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

	res = db_assignment.quiz.dump()
	res['questions'] = [
		question.dump()
		for question
		in db_assignment.quiz.q_select(page=page, seed=db_assignment.rng_seed)
	]

	return JSONResponse(res, status_code=status.HTTP_200_OK)
