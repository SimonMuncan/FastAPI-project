import uuid

from fastapi import FastAPI, HTTPException, Depends
from src.schemas import ProjectDetails, Project
from src.service import SessionLocal
from typing import Generator
from sqlalchemy.orm import Session
from sqlalchemy import select
import src.models as models

app = FastAPI()


def get_db() -> Generator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_project(project_id: uuid.UUID, db: Session) -> ProjectDetails:
    project = db.query(models.Projects).get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"ProjectDetails {project_id} not found")
    return ProjectDetails(project_id=project.id, name=project.name, description=project.description)


def create_project_(project: Project, db: Session) -> ProjectDetails:
    new_project = models.Projects(id=uuid.uuid4(), name=project.name, description=project.description)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return ProjectDetails(**new_project.__dict__)


def get_projects_(db: Session) -> list[ProjectDetails]:
    projects = db.execute(select(models.Projects)).scalars().all()
    return [
        ProjectDetails(
            project_id=uuid.UUID(str(project.id)), name=str(project.name), description=str(project.description)
        )
        for project in projects
    ]


def update_project_details_(project: ProjectDetails, project_data: Project, db: Session) -> ProjectDetails:
    if project_data.name:
        project.name = project_data.name
    if project_data.description:
        project.description = project_data.description

    db.commit()
    db.refresh(project)
    return project


def delete_project_(project: ProjectDetails, db: Session) -> ProjectDetails:
    db.delete(project)
    db.commit()
    return project


@app.get("/projects")
async def get_projects(db: Session = Depends(get_db)) -> list[ProjectDetails]:
    return get_projects_(db)


@app.post("/projects", status_code=201)
async def create_project(project: Project, db: Session = Depends(get_db)) -> ProjectDetails:
    return create_project_(project, db)


@app.get("/project/{project_id}/info")
async def get_project_details(project_id: uuid.UUID, db: Session = Depends(get_db)) -> ProjectDetails:
    return get_project(project_id, db)


@app.put("/project/{project_id}/info")
async def update_project_details(
    project_id: uuid.UUID, project_data: Project, db: Session = Depends(get_db)
) -> ProjectDetails:
    return update_project_details_(get_project(project_id, db), project_data, db)


@app.delete("/project/{project_id}", status_code=204)
async def delete_project(project_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    delete_project_(get_project(project_id, db), db)
