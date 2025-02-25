import uuid
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as sa_uuid
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.service import Base


class Projects(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(sa_uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String, nullable=False)
    description: Mapped[str] = mapped_column(sa.String, nullable=False)

    users_projects: Mapped[list["UserProject"]] = relationship(back_populates="projects")
    documents: Mapped[list["Documents"]] = relationship(back_populates="project")


class Users(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(sa_uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String, nullable=False)
    email: Mapped[str] = mapped_column(sa.String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(sa.String, nullable=False)

    users_projects: Mapped[list["UserProject"]] = relationship(back_populates="users", cascade="all, delete-orphan")


class UserProject(Base):
    __tablename__ = "user_project"

    id: Mapped[uuid.UUID] = mapped_column(sa_uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(sa_uuid(as_uuid=True), sa.ForeignKey("projects.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(sa_uuid(as_uuid=True), sa.ForeignKey("users.id"))
    is_admin: Mapped[bool] = mapped_column(sa.Boolean, default=False)

    users: Mapped["Users"] = relationship(back_populates="users_projects")
    projects: Mapped["Projects"] = relationship(back_populates="users_projects")

    __table_args__ = (sa.UniqueConstraint("project_id", "is_admin", name="_unique_admin_per_project"),)


class Documents(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(sa_uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(sa_uuid(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False)
    title: Mapped[str] = mapped_column(sa.String, nullable=False)
    file_path: Mapped[str] = mapped_column(sa.String, nullable=False)

    project: Mapped["Projects"] = relationship(back_populates="documents")
