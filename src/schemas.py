import uuid

from pydantic import BaseModel, Field


class Project(BaseModel):
    name: str
    description: str | None = None


class ProjectDetails(Project):
    project_id: uuid.UUID = Field(default_factory=uuid.uuid4)


class User(BaseModel):
    user_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    email: str
    password: str


class Document(BaseModel):
    document_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    title: str
    file_path: str
