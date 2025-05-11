from pydantic import BaseModel, field_validator

class Answer(BaseModel):
	text: str
	correct: bool = False

class Question(BaseModel):
	text: str
	answers: list[Answer] = []
	selected: int = -1					# -1 for no selection, 0-based index

	@field_validator('answers')
	def check_answers(cls, answers: list[Answer]) -> list[Answer]:
		if len(answers) < 2:
			raise ValueError('At least two answers are required')

		if sum(answer.correct for answer in answers) != 1:
			raise ValueError('Exactly one answer must be correct')

		return answers

class Quiz(BaseModel):
	title: str
	question_count: int = 0
	per_page: int = 10
	shuffle_questions: bool = False
	shuffle_answers: bool = False

class QuizDetail(Quiz):
	questions: list[Question] = []

class AnswerSelection(BaseModel):
	question_n: int
	answer_n: int

class SubmitAnswer(BaseModel):
	page_n: int
	answers: list[AnswerSelection] = []

class SubmitResult(BaseModel):
	quiz_completed: bool
	page_completed: bool
