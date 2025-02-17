import uuid
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from src.main import app
from typing import Generator
from src.main import (
    projects,
    get_project,
    create_project_,
    get_projects_,
    update_project_details_,
    delete_project_,
)
from src.schemas import Project, ProjectDetails


@pytest.fixture
def client() -> Generator[TestClient]:
    yield TestClient(app)


@pytest.fixture(autouse=True)
def clear_projects() -> Generator[None]:
    from src.main import projects

    yield
    projects.clear()


@pytest.fixture
def sample_project() -> Generator[Project]:
    yield Project(name="Project 1", description="Test project")


@pytest.fixture
def sample_project_2() -> Generator[ProjectDetails]:
    yield ProjectDetails(project_id=uuid.uuid4(), name="Project 2", description="Another test project")


@pytest.fixture
def created_project(sample_project_2: ProjectDetails) -> Generator[ProjectDetails]:
    from src.main import projects

    projects.append(sample_project_2)
    yield sample_project_2


@pytest.fixture
def created_projects(sample_project: Project, sample_project_2: Project) -> Generator[list[ProjectDetails]]:
    from src.main import projects

    for project in (sample_project, sample_project_2):
        project_details = ProjectDetails(**project.model_dump())
        projects.append(project_details)
    yield projects


def test_create_project(client: TestClient, sample_project: Project) -> None:
    response = client.post("/projects", json=sample_project.model_dump())
    assert response.status_code == 201
    data = response.json()
    expected_data = {
        "name": sample_project.name,
        "description": sample_project.description,
        "project_id": data["project_id"],
    }
    assert data == expected_data


def test_get_projects(client: TestClient, created_projects: list[ProjectDetails]) -> None:
    response = client.get("/projects")
    assert response.status_code == 200
    data = response.json()
    expected_data = [
        {"name": project.name, "description": project.description, "project_id": str(project.project_id)}
        for project in created_projects
    ]
    assert data == expected_data


def test_get_project_details(client: TestClient, created_project: ProjectDetails) -> None:
    response = client.get(f"/project/{created_project.project_id}/info")
    assert response.status_code == 200
    data = response.json()
    expected_data = {
        "name": created_project.name,
        "description": created_project.description,
        "project_id": str(created_project.project_id),
    }
    assert data == expected_data


def test_get_project_details_not_found(client: TestClient) -> None:
    random_uuid = uuid.uuid4()
    response = client.get(f"/project/{random_uuid}/info")
    assert response.status_code == 404
    assert response.json() == {"detail": f"ProjectDetails {random_uuid} not found"}


def test_update_project_details(client: TestClient, created_project: ProjectDetails) -> None:
    project = ProjectDetails(
        project_id=created_project.project_id, name=created_project.name, description=created_project.description
    )
    projects.append(project)
    retrieved_project = get_project(created_project.project_id)
    assert retrieved_project == project

    updated_data = {"name": "Updated Name", "description": "Updated project description"}
    response = client.put(f"/project/{created_project.project_id}/info", json=updated_data)
    assert response.status_code == 200
    data = response.json()
    expected_data = {
        "name": created_project.name,
        "description": created_project.description,
        "project_id": str(created_project.project_id),
    }
    assert data == expected_data


def test_update_project_details_not_found(client: TestClient) -> None:
    random_uuid = uuid.uuid4()
    updated_data = {"name": "Updated Name", "description": "Updated project description"}
    response = client.put(f"/project/{random_uuid}/info", json=updated_data)
    assert response.status_code == 404
    assert response.json() == {"detail": f"ProjectDetails {random_uuid} not found"}


def test_delete_project(client: TestClient, created_project: ProjectDetails) -> None:
    response = client.delete(f"/project/{created_project.project_id}")
    assert response.status_code == 204
    assert response.content == b""


def test_delete_project_not_found(client: TestClient) -> None:
    random_uuid = uuid.uuid4()
    response = client.delete(f"/project/{random_uuid}")
    assert response.status_code == 404
    assert response.json() == {"detail": f"ProjectDetails {random_uuid} not found"}


def test_create_project_() -> None:
    project = Project(name="Test Project", description="Test Description")
    created_project = create_project_(project)
    expected_data = {
        "name": project.name,
        "description": project.description,
        "project_id": created_project.project_id,
    }
    assert created_project.model_dump() == expected_data


def test_get_project_(sample_project_2: ProjectDetails) -> None:
    projects.append(sample_project_2)
    retrieved_project = get_project(sample_project_2.project_id)
    assert retrieved_project == sample_project_2


def test_get_project__not_found() -> None:
    random_uuid = uuid.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        get_project(random_uuid)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == f"ProjectDetails {random_uuid} not found"


def test_get_projects_(sample_project_2: ProjectDetails) -> None:
    projects.append(sample_project_2)
    projects.append(sample_project_2)
    all_projects = get_projects_()
    assert len(all_projects) == 2
    assert all_projects == [sample_project_2, sample_project_2]


def test_update_project_details_(sample_project_2: ProjectDetails) -> None:
    projects.append(sample_project_2)
    updated_project = update_project_details_(sample_project_2, "New Name", "New Description")
    assert updated_project.name == "New Name"
    assert updated_project.description == "New Description"


def test_delete_project_(sample_project_2: ProjectDetails) -> None:
    projects.append(sample_project_2)
    deleted_project = delete_project_(sample_project_2)
    assert deleted_project == sample_project_2
    assert sample_project_2 not in projects
