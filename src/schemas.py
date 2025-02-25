import uuid

from pydantic import BaseModel, Field, EmailStr, AnyUrl


class Project(BaseModel):
    name: str
    description: str


class ProjectDetails(Project):
    project_id: uuid.UUID = Field(default_factory=uuid.uuid4)


class User(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserDetails(User):
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4)


class Token(BaseModel):
    access_token: str
    token_type: str


class Document(BaseModel):
    document_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    title: str
    file_path: AnyUrl
