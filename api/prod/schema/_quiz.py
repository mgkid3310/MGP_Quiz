from pydantic import BaseModel, field_validator

class Answer(BaseModel):
	text: str
	correct: bool = False

class Question(BaseModel):
	text: str
	answers: list[Answer] = []

	@field_validator('answers')
	def check_answers(cls, answers: list[Answer]) -> list[Answer]:
		if len(answers) < 2:
			raise ValueError('At least two answers are required')

		if sum(answer.correct for answer in answers) != 1:
			raise ValueError('Exactly one answer must be correct')

		return answers

class QuestionTest(Question):
	selected: int = -1					# -1 for no selection, 0-based index

class QuizInfo(BaseModel):
	title: str
	question_count: int = 0
	per_page: int = 10
	shuffle_questions: bool = False
	shuffle_answers: bool = False

class QuizForm(QuizInfo):
	questions: list[Question]

class QuizResult(QuizInfo):
	completed: bool = False
	score: int = -1

class QuizTest(QuizInfo):
	questions: list[QuestionTest]

class AnswerSelection(BaseModel):
	question_n: int
	answer_n: int

	@field_validator('question_n', 'answer_n')
	def check_positive(cls, value: int) -> int:
		if value < 0:
			raise ValueError('Value must be positive')

		return value
class SubmitAnswer(BaseModel):
	page_n: int
	answers: list[AnswerSelection]

	@field_validator('answers')
	def check_answers(cls, answers: list[AnswerSelection]) -> list[AnswerSelection]:
		if len(answers) != len(set(ans.question_n for ans in answers)):
			raise ValueError('Duplicate question numbers are not allowed')

		return answers
