from __future__ import annotations
import asyncio, random

from sqlalchemy import BOOLEAN, INTEGER, REAL, CHAR, VARCHAR, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from tsidpy import TSID, TSIDGenerator

from ._engine import create_engine

def generate_uid() -> str:
	return TSIDGenerator().create().to_string()

def increment_uid(uid: str, num: int = 1) -> str:
	tsid = TSID.from_string(uid)
	return TSID(tsid.number + num).to_string()

def rng_seed() -> int:
	return random.randint(0, 2**31 - 1)

class UIDGenerator:
	def __init__(self, ordered: bool = False) -> None:
		self.uid = generate_uid()
		self.ordered = ordered

	def create(self) -> str:
		if self.ordered:
			self.uid = increment_uid(self.uid)
		else:
			self.uid = generate_uid()

		return self.uid

class Base(DeclarativeBase):
	pass

class User(Base):
	__tablename__ = 'user'

	# pk
	uid: Mapped[str] = mapped_column(CHAR(13), primary_key=True, default=generate_uid)

	# attributes
	username: Mapped[str] = mapped_column(VARCHAR(64), index=True)
	hashed_pw: Mapped[str] = mapped_column(VARCHAR(72))
	is_admin: Mapped[bool] = mapped_column(BOOLEAN, default=False)

	# 1-to-N
	assignments: Mapped[list[Assignment]] = relationship(
		'Assignment',
		back_populates='user'
	)

class Quiz(Base):
	__tablename__ = 'quiz'

	# pk
	uid: Mapped[str] = mapped_column(CHAR(13), primary_key=True, default=generate_uid)

	# attributes
	title: Mapped[str] = mapped_column(VARCHAR(256), index=True)
	question_count: Mapped[int] = mapped_column(INTEGER, default=0)
	per_page: Mapped[int] = mapped_column(INTEGER, default=10)

	shuffle_questions: Mapped[bool] = mapped_column(BOOLEAN, default=False)
	shuffle_answers: Mapped[bool] = mapped_column(BOOLEAN, default=False)

	# 1-to-N
	assignments: Mapped[list[Assignment]] = relationship(
		'Assignment',
		back_populates='quiz'
	)
	questions: Mapped[list[Question]] = relationship(
		'Question',
		back_populates='quiz',
		lazy='selectin'
	)

	def q_select(
		self,
		page: int = 0,
		seed: int | None = None,
		admin: bool = False
	) -> list[Question]:
		question_count = self.question_count if not admin else len(self.questions)

		if question_count > len(self.questions):
			raise ValueError('Question count exceeds available questions')

		if seed is None:
			seed = rng_seed()

		rng = random.Random(seed)

		if self.shuffle_questions and not admin:
			questions = rng.sample(self.questions, question_count)
		else:
			questions = sorted(self.questions, key=lambda q: q.uid)
			questions = questions[:question_count]

		idx_l, idx_r = self.per_page * page, self.per_page * (page + 1)
		idx_l = max(0, idx_l)
		idx_r = min(len(questions), idx_r)

		questions = questions[idx_l:idx_r]

		if self.shuffle_answers and not admin:
			for question in questions:
				rng.shuffle(question.answers)
		else:
			for question in questions:
				question.answers = sorted(question.answers, key=lambda a: a.uid)

		return questions

	def dump(self) -> dict:
		return {
			'title': self.title,
			'question_count': self.question_count,
			'per_page': self.per_page,
			'shuffle_questions': self.shuffle_questions,
			'shuffle_answers': self.shuffle_answers
		}

class Question(Base):
	__tablename__ = 'question'

	# pk
	uid: Mapped[str] = mapped_column(CHAR(13), primary_key=True, default=generate_uid)

	# fks
	quiz_uid: Mapped[str] = mapped_column(CHAR(13), ForeignKey('quiz.uid'), index=True)

	# attributes
	text: Mapped[str] = mapped_column(VARCHAR(512))

	# N-to-1
	quiz: Mapped[Quiz] = relationship(
		'Quiz',
		back_populates='questions',
		lazy='selectin'
	)

	# 1-to-N
	answers: Mapped[list[Answer]] = relationship(
		'Answer',
		back_populates='question',
		lazy='selectin'
	)

	def dump(self) -> dict:
		answers = sorted(self.answers, key=lambda a: a.uid)

		return {
			'text': self.text,
			'answers': [answer.dump() for answer in answers]
		}

class Answer(Base):
	__tablename__ = 'answer'

	# pk
	uid: Mapped[str] = mapped_column(CHAR(13), primary_key=True, default=generate_uid)

	# fks
	question_uid: Mapped[str] = mapped_column(CHAR(13), ForeignKey('question.uid'), index=True)

	# attributes
	text: Mapped[str] = mapped_column(VARCHAR(256))
	correct: Mapped[bool] = mapped_column(BOOLEAN, default=False)

	# 1-to-N
	submissions: Mapped[list[Submission]] = relationship(
		'Submission',
		back_populates='answer'
	)

	# N-to-1
	question: Mapped[Question] = relationship(
		'Question',
		back_populates='answers',
		lazy='selectin'
	)

	def dump(self) -> dict:
		return {
			'text': self.text,
			'correct': self.correct
		}

class Assignment(Base):
	__tablename__ = 'assignment'

	# pk
	user_uid: Mapped[str] = mapped_column(CHAR(13), ForeignKey('user.uid'), primary_key=True)
	quiz_uid: Mapped[str] = mapped_column(CHAR(13), ForeignKey('quiz.uid'), primary_key=True)

	# attributes
	rng_seed: Mapped[int] = mapped_column(INTEGER, default=rng_seed)
	completed: Mapped[bool] = mapped_column(BOOLEAN, default=False)
	score: Mapped[float] = mapped_column(REAL, default=-1.0)

	# N-to-1
	user: Mapped[User] = relationship(
		'User',
		back_populates='assignments'
	)
	quiz: Mapped[Quiz] = relationship(
		'Quiz',
		back_populates='assignments',
		lazy='selectin'
	)

class Submission(Base):
	__tablename__ = 'submission'

	# pk
	user_uid: Mapped[str] = mapped_column(CHAR(13), ForeignKey('user.uid'), primary_key=True)
	question_uid: Mapped[str] = mapped_column(CHAR(13), ForeignKey('question.uid'), primary_key=True)

	# fks
	answer_uid: Mapped[str] = mapped_column(CHAR(13), ForeignKey('answer.uid'), index=True)

	# N-to-1
	answer: Mapped[Answer] = relationship(
		'Answer',
		back_populates='submissions',
		lazy='selectin'
	)

async def create_tables() -> None:
	async with create_engine().begin() as connection:
		await connection.run_sync(Base.metadata.create_all)

try:
	loop = asyncio.get_running_loop()
except RuntimeError:
	loop = asyncio.new_event_loop()
	asyncio.set_event_loop(loop)

if loop.is_running():
	loop.create_task(create_tables())
else:
	loop.run_until_complete(create_tables())
