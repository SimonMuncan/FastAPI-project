import uuid
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as sa_di
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Projects(Base):
    __tablename__ = "projects"

    id = sa.Column(sa_di.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = sa.Column(sa.String, nullable=False)
    description = sa.Column(sa.String, nullable=True)
    users_projects = relationship("UserProject", back_populates="projects")
    documents = relationship("Documents", back_populates="project")


class Users(Base):
    __tablename__ = "users"

    id = sa.Column(sa_di.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = sa.Column(sa.String, nullable=False)
    email = sa.Column(sa.String, unique=True, nullable=False)
    hashed_password = sa.Column(sa.String, nullable=False)
    users_projects = relationship("UserProject", back_populates="users", cascade="all, delete-orphan")


class UserProject(Base):
    __tablename__ = "user_project"

    project_id = sa.Column(sa_di.UUID(as_uuid=True), sa.ForeignKey("projects.id"), primary_key=True)
    user_id = sa.Column(sa_di.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True)
    is_admin = sa.Column(sa.Boolean, default=False)
    users = relationship("Users", back_populates="users_projects")
    projects = relationship("Projects", back_populates="users_projects")
    __table_args__ = (
        sa.Index("idx_admin_per_project", "project_id", unique=True, postgresql_where=sa.text("is_admin = true")),
    )


class Documents(Base):
    __tablename__ = "documents"

    id = sa.Column(sa_di.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = sa.Column(sa_di.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False)
    title = sa.Column(sa.String, nullable=False)
    file_path = sa.Column(sa.String, nullable=False)
    project = relationship("Projects", back_populates="documents")
