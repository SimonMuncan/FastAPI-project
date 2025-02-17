import uuid

from pydantic import BaseModel, Field


class Project(BaseModel):
    name: str
    description: str | None = None


class ProjectDetails(Project):
    project_id: uuid.UUID = Field(default_factory=uuid.uuid4)
