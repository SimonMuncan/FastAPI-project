import uuid

from pydantic import AnyUrl, BaseModel, EmailStr, Field


class Project(BaseModel):
    name: str
    description: str | None = None


class ProjectDetails(Project):
    project_id: uuid.UUID = Field(default_factory=uuid.uuid4)


class User(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=8)


class UserDetails(User):
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4)


class Document(BaseModel):
    document_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    title: str
    file_path: AnyUrl


class OAuth2TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int | None = None
    refresh_token: str | None = None
    scope: str | None = None


class CurrentUser(BaseModel):
    id: uuid.UUID
    email: str
