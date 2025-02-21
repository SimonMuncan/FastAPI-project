import uuid
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session

from src.schemas import ProjectDetails, Project
from src.service import (
    get_projects_,
    create_project_,
    get_project,
    update_project_details_,
    delete_project_,
    get_session,
)

app = FastAPI()


@app.get("/projects")
async def get_projects(db: Session = Depends(get_session)) -> list[ProjectDetails]:
    return [
        ProjectDetails(project_id=project.id, name=project.name, description=project.description)
        for project in get_projects_(db)
    ]


@app.post("/projects", status_code=201)
async def create_project(project: Project, db: Session = Depends(get_session)) -> ProjectDetails:
    return ProjectDetails(**create_project_(project, db).__dict__)


@app.get("/project/{project_id}/info")
async def get_project_details(project_id: uuid.UUID, db: Session = Depends(get_session)) -> ProjectDetails:
    project = get_project(project_id, db)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return ProjectDetails(**project.__dict__)


@app.put("/project/{project_id}/info")
async def update_project_details(
    project_id: uuid.UUID, project_data: Project, db: Session = Depends(get_session)
) -> None:
    project = get_project(project_id, db)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    update_project_details_(project, project_data, db)


@app.delete("/project/{project_id}", status_code=204)
async def delete_project(project_id: uuid.UUID, db: Session = Depends(get_session)) -> None:
    project = get_project(project_id, db)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    delete_project_(project, db)
