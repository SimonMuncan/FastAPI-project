from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_create_project() -> None:
    new_project = {"project_id": 1, "name": "Project 1", "description": "This is a test project"}

    response = client.post("/projects/", json=new_project)

    assert response.status_code == 200
    assert response.json() == new_project


def test_get_all_projects() -> None:
    response = client.get("/projects/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0


def test_get_project_details() -> None:
    new_project = {"project_id": 2, "name": "Project 2", "description": "Another test project"}

    client.post("/projects/", json=new_project)

    response = client.get("/project/2/info")

    assert response.status_code == 200
    assert response.json() == new_project


def test_get_project_details_not_found() -> None:
    response = client.get("/project/999/info")

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}


def test_update_project_details() -> None:
    updated_description = "Updated project description"

    response = client.put("/project/2/info", params={"description": updated_description})

    assert response.status_code == 200
    assert response.json()["description"] == updated_description


def test_update_project_details_not_found() -> None:
    updated_description = "Updated project description"

    response = client.put("/project/999/info", params={"description": updated_description})

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}


def test_delete_project() -> None:
    new_project = {"project_id": 3, "name": "Project 3", "description": "Project to be deleted"}

    client.post("/projects/", json=new_project)

    response = client.delete("/project/3/")

    assert response.status_code == 200
    assert response.json() == {"message": "Deleted project"}


def test_delete_project_not_found() -> None:
    response = client.delete("/project/999/")

    assert response.status_code == 404
    assert response.json() == {"detail": "Project not found"}
