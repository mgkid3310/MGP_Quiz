from . import _admin
from . import _user

routers = [
	_admin.router,
	_user.router
]

__all__ = [
	'routers'
]
