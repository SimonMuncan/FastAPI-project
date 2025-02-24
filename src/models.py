import uuid
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as sa_uuid
from sqlalchemy.orm import relationship

from src.service import Base


class Projects(Base):
    __tablename__ = "projects"

    id = sa.Column(sa_uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = sa.Column(sa.String, nullable=False)
    description = sa.Column(sa.String, nullable=False)
    users_projects = relationship("UserProject", back_populates="projects")
    documents = relationship("Documents", back_populates="project")


class Users(Base):
    __tablename__ = "users"

    id = sa.Column(sa_uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = sa.Column(sa.String, nullable=False)
    email = sa.Column(sa.String, unique=True, nullable=False)
    hashed_password = sa.Column(sa.String, nullable=False)
    users_projects = relationship("UserProject", back_populates="users", cascade="all, delete-orphan")


class UserProject(Base):
    __tablename__ = "user_project"

    id = sa.Column(sa_uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = sa.Column(sa_uuid(as_uuid=True), sa.ForeignKey("projects.id"))
    user_id = sa.Column(sa_uuid(as_uuid=True), sa.ForeignKey("users.id"))
    is_admin = sa.Column(sa.Boolean, default=False)
    users = relationship("Users", back_populates="users_projects")
    projects = relationship("Projects", back_populates="users_projects")
    __table_args__ = (sa.UniqueConstraint("project_id", "is_admin", name="_unique_admin_per_project"),)


class Documents(Base):
    __tablename__ = "documents"

    id = sa.Column(sa_uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = sa.Column(sa_uuid(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False)
    title = sa.Column(sa.String, nullable=False)
    file_path = sa.Column(sa.String, nullable=False)
    project = relationship("Projects", back_populates="documents")
