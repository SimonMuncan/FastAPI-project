import uuid
from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.service import Base


class Projects(Base):
    __tablename__ = "projects"

    project_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True)
    description = Column(String, index=True)
    user_projects = relationship("UserProject", back_populates="project")
    document = relationship("Documents", back_populates="project")


class Users(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    user_projects = relationship("UserProject", back_populates="user", cascade="all, delete-orphan")


class UserProject(Base):
    __tablename__ = "m2m_user_project"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    project_admin = Column(Boolean, default=False)
    user = relationship("Users", back_populates="user_projects")
    project = relationship("Projects", back_populates="user_projects")


class Documents(Base):
    __tablename__ = "documents"

    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    title = name = Column(String, index=True)
    file_path = Column(String, nullabke=False)
    project = relationship("Projects", back_populates="documents")
