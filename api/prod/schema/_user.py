from pydantic import BaseModel

class UserBase(BaseModel):
	username: str

class UserCreate(UserBase):
	password: str

class UserPasswordUpdate(BaseModel):
	password: str

class TokenAccess(BaseModel):
	access_token: str
	is_admin: bool
