from pydantic import BaseModel, field_validator

class UID(BaseModel):
	uid: str

class Answer(BaseModel):
	text: str
	correct: bool = False

class QuestionView(BaseModel):
	text: str
	answers: list[Answer] = []

	@field_validator('answers')
	def check_answers(cls, answers: list[Answer]) -> list[Answer]:
		if len(answers) < 2:
			raise ValueError('At least two answers are required')

		if sum(answer.correct for answer in answers) != 1:
			raise ValueError('Exactly one answer must be correct')

		return answers

class QuestionTest(QuestionView):
	selected: int = -1					# -1 for no selection, 0-based index

class QuizBase(BaseModel):
	title: str
	question_count: int = 0
	per_page: int = 10
	shuffle_questions: bool = False
	shuffle_answers: bool = False

class QuizForm(QuizBase):
	questions: list[QuestionView]

class QuizViewAdmin(UID, QuizBase):
	pass

class QuizViewStudent(QuizViewAdmin):
	completed: bool = False
	score: int = -1

class QuizViewTest(UID, QuizBase):
	questions: list[QuestionTest]

class AnswerSelection(BaseModel):
	question_idx: int
	answer_idx: int

	@field_validator('question_idx', 'answer_idx')
	def check_positive(cls, value: int) -> int:
		if value < 0:
			raise ValueError('Value must be positive')

		return value
class SubmitAnswer(BaseModel):
	page_idx: int
	answers: list[AnswerSelection]

	@field_validator('answers')
	def check_answers(cls, answers: list[AnswerSelection]) -> list[AnswerSelection]:
		if len(answers) != len(set(ans.question_idx for ans in answers)):
			raise ValueError('Duplicate question numbers are not allowed')

		return answers
