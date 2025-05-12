from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import Response, JSONResponse

import auth, database, schema

router = APIRouter(tags=['Quiz - Admin'])

@router.post('/admin/promote', status_code=status.HTTP_200_OK)
async def promote_user(
	code: str = Depends(auth.query('code')),
	token: str = Depends(auth.oauth2),
	db: database.DB = Depends(database.provide_db)
) -> Response:
	if not auth.confirm_code(code):
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

	db_user = await auth.jwt2user(db, token)
	db_user.is_admin = True

	return Response(status_code=status.HTTP_200_OK)

@router.get('/admin/quiz', response_model=dict[str, schema.quiz.QuizInfo])
async def get_all_quizzes(
	token: str = Depends(auth.oauth2),
	db: database.DB = Depends(database.provide_db)
) -> Response:
	await auth.jwt2user(db, token, admin=True)

	quizzes = await db.query_list(database.models.Quiz)

	return JSONResponse(
		{quiz.uid: quiz.dump() for quiz in quizzes},
		status_code=status.HTTP_200_OK
	)

@router.post('/admin/quiz', response_model=str, status_code=status.HTTP_201_CREATED)
async def create_quiz(
	body: schema.quiz.QuizForm,
	token: str = Depends(auth.oauth2),
	db: database.DB = Depends(database.provide_db)
) -> Response:
	await auth.jwt2user(db, token, admin=True)

	uid_generator = database.models.UIDGenerator(ordered=True)

	db_quiz = database.models.Quiz(
		uid=uid_generator.create(),
		title=body.title,
		question_count=body.question_count,
		per_page=body.per_page,
		shuffle_questions=body.shuffle_questions,
		shuffle_answers=body.shuffle_answers
	)

	for question in body.questions:
		db_question = database.models.Question(
			uid=uid_generator.create(),
			quiz_uid=db_quiz.uid,
			text=question.text
		)
		db.session.add(db_question)

		for answer in question.answers:
			db_answer = database.models.Answer(
				uid=uid_generator.create(),
				question_uid=db_question.uid,
				text=answer.text,
				correct=answer.correct
			)
			db.session.add(db_answer)

	db.session.add(db_quiz)

	return Response(db_quiz.uid, status_code=status.HTTP_201_CREATED)

@router.get('/admin/quiz/{uid}', response_model=schema.quiz.QuizInfo)
async def get_quiz_details(
	uid: str = Depends(auth.path('uid')),
	token: str = Depends(auth.oauth2),
	db: database.DB = Depends(database.provide_db)
) -> Response:
	await auth.jwt2user(db, token, admin=True)

	db_quiz = await db.query_item(database.models.Quiz, uid=uid)

	if not db_quiz:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

	return JSONResponse(db_quiz.dump(), status_code=status.HTTP_200_OK)

@router.get('/admin/quiz/{uid}/questions', response_model=schema.quiz.QuizForm)
async def get_quiz_full_questions(
	uid: str = Depends(auth.path('uid')),
	page: int = Query(0, ge=0),
	token: str = Depends(auth.oauth2),
	db: database.DB = Depends(database.provide_db)
) -> Response:
	await auth.jwt2user(db, token, admin=True)

	db_quiz = await db.query_item(database.models.Quiz, uid=uid)

	if not db_quiz:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

	res = db_quiz.dump()
	res['questions'] = [
		question.dump()
		for question
		in db_quiz.q_select(page=page, admin=True)
	]

	return JSONResponse(res, status_code=status.HTTP_200_OK)

@router.post('/admin/assign', response_model=None, status_code=status.HTTP_201_CREATED)
async def assign_quiz(
	user_uid: str = Depends(auth.query('user')),
	quiz_uid: str = Depends(auth.query('quiz')),
	token: str = Depends(auth.oauth2),
	db: database.DB = Depends(database.provide_db)
) -> Response:
	await auth.jwt2user(db, token, admin=True)

	db_user = await db.query_item(database.models.User, uid=user_uid)
	db_quiz = await db.query_item(database.models.Quiz, uid=quiz_uid)

	if not db_user or not db_quiz:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

	db_assignment = database.models.Assignment(
		user_uid=db_user.uid,
		quiz_uid=db_quiz.uid
	)
	db.session.add(db_assignment)

	return Response(status_code=status.HTTP_201_CREATED)
