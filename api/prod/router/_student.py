from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import Response, JSONResponse

import auth, database, schema

router = APIRouter(tags=['Quiz - Student'])

@router.get('/student/quiz', response_model=dict[str, schema.quiz.QuizResult])
async def get_assigned_quizzes(
	token: str = Depends(auth.oauth2),
	db: database.DB = Depends(database.provide_db)
) -> Response:
	db_user = await auth.jwt2user(db, token)

	await db.session.run_sync(lambda s: s.refresh(db_user, ['assignments']))

	res = {}
	for assignment in db_user.assignments:
		res[assignment.quiz.uid] = assignment.quiz.dump()
		res[assignment.quiz.uid]['completed'] = assignment.completed
		res[assignment.quiz.uid]['score'] = assignment.score

	return JSONResponse(res, status_code=status.HTTP_200_OK)

@router.get('/student/quiz/{uid}', response_model=schema.quiz.QuizResult)
async def get_quiz_details(
	uid: str = Depends(auth.path('uid')),
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
	res['completed'] = db_assignment.completed
	res['score'] = db_assignment.score

	return JSONResponse(res, status_code=status.HTTP_200_OK)

@router.get('/student/quiz/{uid}/questions', response_model=schema.quiz.QuizTest)
async def get_quiz_questions(
	uid: str = Depends(auth.path('uid')),
	page: int = Query(0, ge=0),
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

	db_subs = await db.query_list(
		database.models.Submission,
		user_uid=db_user.uid,
		question_uid=[q.uid for q in db_assignment.quiz.questions]
	)
	q2sub = {sub.question_uid: sub for sub in db_subs}
	db_questions = db_assignment.quiz.q_select(page=page, seed=db_assignment.rng_seed)

	questions = []
	for question in db_questions:
		questions.append(question.dump())
		questions[-1]['selected'] = -1

		if question.uid in q2sub.keys():
			sub = q2sub[question.uid]
			questions[-1]['selected'] = question.answers.index(sub.answer)

	res = db_assignment.quiz.dump()
	res['questions'] = questions

	return JSONResponse(res, status_code=status.HTTP_200_OK)

@router.post('/student/quiz/{uid}/submit', response_model=None, status_code=status.HTTP_200_OK)
async def submit_answer(
	body: schema.quiz.SubmitAnswer,
	uid: str = Depends(auth.path('uid')),
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

	if db_assignment.completed:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail='Quiz has already been graded'
		)

	curr_q = db_assignment.quiz.q_select(
		page=body.page_n,
		seed=db_assignment.rng_seed
	)

	ans_subs = await db.query_list(
		database.models.Submission,
		user_uid=db_user.uid,
		question_uid=[q.uid for q in curr_q]
	)
	sub_dict = {a.question_uid: a for a in ans_subs}

	for ans in body.answers:
		if ans.question_n >= len(curr_q):
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail='Question number out of range'
			)

		question = curr_q[ans.question_n]
		if ans.answer_n >= len(question.answers):
			raise HTTPException(
				status_code=status.HTTP_400_BAD_REQUEST,
				detail='Answer number out of range'
			)

		question.shuffle_ans(db_assignment.rng_seed)
		ans_uid = question.answers[ans.answer_n].uid
		if question.uid in sub_dict.keys():
			sub_dict[question.uid].answer_uid = ans_uid
		else:
			new_sub = database.models.Submission(
				user_uid=db_user.uid,
				question_uid=question.uid,
				answer_uid=ans_uid
			)
			db.session.add(new_sub)
			sub_dict[question.uid] = new_sub

	return Response(status_code=status.HTTP_200_OK)

@router.post('/student/quiz/{uid}/grade', response_model=None, status_code=status.HTTP_200_OK)
async def grade_quiz(
	uid: str = Depends(auth.path('uid')),
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

	if db_assignment.completed:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail='Quiz has already been graded'
		)

	db_subs = await db.query_list(
		database.models.Submission,
		user_uid=db_user.uid,
		question_uid=[q.uid for q in db_assignment.quiz.questions]
	)

	if len(db_subs) != db_assignment.quiz.question_count:
		raise HTTPException(
			status_code=status.HTTP_400_BAD_REQUEST,
			detail='Not all questions have been answered'
		)

	db_assignment.completed = True
	db_assignment.score = sum(db_sub.answer.correct for db_sub in db_subs)

	return Response(status_code=status.HTTP_200_OK)
