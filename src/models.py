import uuid
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as sa_di
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Projects(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(sa_di.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String, nullable=False)
    description: Mapped[str] = mapped_column(sa.String, nullable=True)
    users_projects: Mapped[list["UserProject"]] = relationship("UserProject", back_populates="projects")
    documents: Mapped[list["Documents"]] = relationship("Documents", back_populates="project")


class Users(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(sa_di.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(sa.String, nullable=False)
    email: Mapped[str] = mapped_column(sa.String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(sa.String, nullable=False)
    users_projects: Mapped[list["UserProject"]] = relationship(
        "UserProject", back_populates="users", cascade="all, delete-orphan"
    )


class UserProject(Base):
    __tablename__ = "user_project"

    project_id: Mapped[uuid.UUID] = mapped_column(
        sa_di.UUID(as_uuid=True), sa.ForeignKey("projects.id"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(sa_di.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True)
    is_admin: Mapped[bool] = mapped_column(sa.Boolean, default=False)
    users: Mapped["Users"] = relationship("Users", back_populates="users_projects")
    projects: Mapped["Projects"] = relationship("Projects", back_populates="users_projects")
    __table_args__ = (
        sa.Index("idx_admin_per_project", "project_id", unique=True, postgresql_where=sa.text("is_admin = true")),
    )


class Documents(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(sa_di.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        sa_di.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(sa.String, nullable=False)
    file_path: Mapped[str] = mapped_column(sa.String, nullable=False)
    project: Mapped["Projects"] = relationship("Projects", back_populates="documents")
