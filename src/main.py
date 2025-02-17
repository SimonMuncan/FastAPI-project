from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


class Project(BaseModel):
    project_id: int
    name: str
    description: str | None = None


app = FastAPI()
users = [{"name": "Simon", "id": "1"}]
projects = []


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}


@app.post("/projects/")
async def create_project(project: Project) -> object:
    projects.append(project)
    return project


@app.get("/projects/")
async def get_all_projects() -> list:
    return projects


@app.get("/project/{project_id}/info")
async def get_project_details(project_id: int) -> object:
    project = next((p for p in projects if p.project_id == project_id), None)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.put("/project/{project_id}/info")
async def update_project_details(project_id: int, description: str) -> object:
    project = next((p for p in projects if p.project_id == project_id), None)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    project.description = description
    return project


@app.delete("/project/{project_id}/")
async def delete_project(project_id: int) -> dict[str, str]:
    project = next((p for p in projects if p.project_id == project_id), None)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    projects.remove(project)
    return {"message": "Deleted project"}
