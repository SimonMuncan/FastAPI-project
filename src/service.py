from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import uuid
from dotenv import load_dotenv
from typing import Generator, Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.models import Projects
from src.schemas import Project

load_dotenv()

POSTGRES_USER = os.environ.get("POSTGRES_USER", "")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
POSTGRES_SERVER = os.environ.get("POSTGRES_SERVER", "localhost")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session() -> Generator[Session]:
    with SessionLocal() as session:
        yield session


def get_project(project_id: uuid.UUID, db: Session) -> Projects | None:
    return db.query(Projects).get(project_id)


def create_project_(project: Project, db: Session) -> Projects:
    new_project = Projects(name=project.name, description=project.description)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project


def get_projects_(db: Session) -> Sequence[Projects]:
    return db.execute(select(Projects)).scalars().all()


def update_project_details_(project: Projects, project_data: Project, db: Session) -> None:
    project = db.merge(project)
    if project_data.name:
        project.name = project_data.name
    if project_data.description:
        project.description = project_data.description

    db.commit()
    db.refresh(project)


def delete_project_(project: Projects, db: Session) -> None:
    db.delete(project)
    db.commit()
