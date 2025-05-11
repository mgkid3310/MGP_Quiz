from . import _admin
from . import _student
from . import _user

routers = [
	_admin.router,
	_student.router,
	_user.router
]

__all__ = [
	'routers'
]
