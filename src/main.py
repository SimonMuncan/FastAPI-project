import uuid

from fastapi import FastAPI, HTTPException
from src.schemas import ProjectDetails, Project

app = FastAPI()
projects: list[ProjectDetails] = []


def get_project(project_id: uuid.UUID) -> ProjectDetails:
    project = next((p for p in projects if p.project_id == project_id), None)
    if project is None:
        raise HTTPException(status_code=404, detail=f"ProjectDetails {project_id} not found")
    return project


def create_project_(project: Project) -> ProjectDetails:
    new_project = ProjectDetails(**project.model_dump())
    projects.append(new_project)
    return new_project


def get_projects_() -> list[ProjectDetails]:
    return projects


def update_project_details_(project: ProjectDetails, name: str, description: str | None) -> ProjectDetails:
    project.description = description
    project.name = name
    return project


def delete_project_(project: ProjectDetails) -> ProjectDetails:
    projects.remove(project)
    return project


@app.get("/projects")
async def get_projects() -> list[ProjectDetails]:
    return get_projects_()


@app.post("/projects", status_code=201)
async def create_project(project: Project) -> ProjectDetails:
    return create_project_(project)


@app.get("/project/{project_id}/info")
async def get_project_details(project_id: uuid.UUID) -> ProjectDetails:
    return get_project(project_id)


@app.put("/project/{project_id}/info")
async def update_project_details(project_id: uuid.UUID, project_data: Project) -> ProjectDetails:
    return update_project_details_(get_project(project_id), project_data.name, project_data.description)


@app.delete("/project/{project_id}", status_code=204)
async def delete_project(project_id: uuid.UUID) -> None:
    delete_project_(get_project(project_id))
