import uuid
from unittest import mock
import pytest
from typing import Generator
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from src.schemas import ProjectDetails, Project
import src.models as models
from src.service import get_session, delete_project_, update_project_details_, get_projects_, get_project
from src.main import app


@pytest.fixture(autouse=True)
def mock_db_config():
    with mock.patch.multiple(
        "src.service",
        POSTGRES_USER="test_user",
        POSTGRES_PASSWORD="test_password",
        POSTGRES_DB="test_db",
        POSTGRES_PORT="5432",
        POSTGRES_SERVER="localhost",
        DATABASE_URL="postgresql://test_user:test_password@localhost:5432/test_db",
    ):
        yield


@pytest.fixture
def mock_db() -> Generator[MagicMock]:
    with patch("src.service.SessionLocal") as session_patcher:
        db_mock = MagicMock()
        session_patcher.return_value = db_mock
        yield db_mock


@pytest.fixture
def override_get_db(mock_db: MagicMock) -> Generator[None]:
    app.dependency_overrides[get_session] = lambda: (yield mock_db)
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def mock_project() -> Generator[models.Projects]:
    yield models.Projects(id=uuid.uuid4(), name="Test Project", description="Test Description")


@pytest.fixture
def mock_project_2() -> Generator[ProjectDetails]:
    yield ProjectDetails(project_id=uuid.uuid4(), name="Test Project", description="Test Description")


@pytest.fixture
def project_data() -> Generator[Project]:
    yield Project(name="Test Project", description="Test Description")


@pytest.fixture
def client(override_get_db: MagicMock) -> Generator[TestClient]:
    yield TestClient(app)


def test_get_projects(client: TestClient, mock_db: MagicMock, mock_project: models.Projects) -> None:
    mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_project]
    response = client.get("/projects")
    assert response.status_code == 200
    expected_data = [
        {"project_id": str(mock_project.id), "name": mock_project.name, "description": mock_project.description}
    ]
    assert response.json() == expected_data


def test_create_project(
    client: TestClient, mock_db: MagicMock, project_data: Project, mock_project: models.Projects
) -> None:
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()
    response = client.post("/projects", json=project_data.model_dump())
    response_json = response.json()
    expected_data = {
        "project_id": response_json["project_id"],
        "name": mock_project.name,
        "description": mock_project.description,
    }
    assert response.status_code == 201
    assert response_json == expected_data


def test_get_project_details_success(client: TestClient, mock_db: MagicMock, mock_project: models.Projects) -> None:
    project_id = mock_project.id
    mock_db.query.return_value.get.return_value = mock_project
    response = client.get(f"/project/{project_id}/info")
    response_json = response.json()
    expected_data = {
        "project_id": response_json["project_id"],
        "name": mock_project.name,
        "description": mock_project.description,
    }
    assert response.status_code == 200
    assert response_json == expected_data
    mock_db.query.assert_called_once()


def test_get_project_details_not_found(client: TestClient, mock_db: MagicMock) -> None:
    project_id = uuid.uuid4()
    mock_db.query.return_value.get.return_value = None
    response = client.get(f"/project/{project_id}/info")
    assert response.status_code == 404
    assert response.json() == {"detail": f"Project {project_id} not found"}
    mock_db.query.assert_called_once()


def test_update_project_details_success(
    client: TestClient, mock_db: MagicMock, mock_project: models.Projects, project_data: Project
) -> None:
    project_id = mock_project.id
    mock_db.query.return_value.get.return_value = mock_project
    mock_db.merge.return_value = mock_project
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()
    response = client.put(f"/project/{project_id}/info", json=project_data.model_dump())
    assert response.status_code == 200
    mock_db.query.assert_called_once()


def test_update_project_details_not_found(client: TestClient, mock_db: MagicMock, project_data: Project) -> None:
    project_id = uuid.uuid4()
    mock_db.query.return_value.get.return_value = None
    response = client.put(f"/project/{project_id}/info", json=project_data.model_dump())
    assert response.status_code == 404
    assert response.json() == {"detail": f"Project {project_id} not found"}
    mock_db.query.assert_called_once()


def test_delete_project_success(client: TestClient, mock_db: MagicMock, mock_project: models.Projects) -> None:
    project_id = mock_project.id
    mock_db.query.return_value.get.return_value = mock_project
    mock_db.delete = MagicMock()
    mock_db.commit = MagicMock()
    response = client.delete(f"/project/{project_id}")
    assert response.status_code == 204
    assert response.content == b""
    mock_db.query.assert_called_once()


def test_delete_project_not_found(client: TestClient, mock_db: MagicMock) -> None:
    project_id = uuid.uuid4()
    mock_db.query.return_value.get.return_value = None
    response = client.delete(f"/project/{project_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": f"Project {project_id} not found"}
    mock_db.query.assert_called_once()


def test_get_project_(mock_db: MagicMock, mock_project: models.Projects, mock_project_2: ProjectDetails) -> None:
    mock_db.query.return_value.get.return_value = mock_project
    result = get_project(mock_project.id, mock_db)

    assert result is not None
    assert ProjectDetails(project_id=result.id, name=result.name, description=result.description) == ProjectDetails(
        project_id=mock_project.id, name=mock_project.name, description=mock_project.description
    )


def test_get_projects_(mock_db: MagicMock, mock_project: models.Projects) -> None:
    mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_project]
    result = get_projects_(mock_db)
    result_as_schemas = [
        ProjectDetails(
            project_id=proj.id,
            name=proj.name,
            description=proj.description,
        )
        for proj in result
    ]
    expected_result = [
        ProjectDetails(
            project_id=result[0].id,
            name=mock_project.name,
            description=mock_project.description,
        )
    ]
    assert result_as_schemas == expected_result


def test_update_project_details_(mock_db: MagicMock, mock_project: models.Projects) -> None:
    project_data = Project(name="New Name", description="New Description")
    mock_db.merge.return_value = mock_project
    update_project_details_(mock_project, project_data, mock_db)
    expected_result = ProjectDetails(
        project_id=mock_project.id, name=project_data.name, description=project_data.description
    )
    result = ProjectDetails(project_id=mock_project.id, name=mock_project.name, description=mock_project.description)
    assert result == expected_result


def test_delete_project_(mock_db: MagicMock, mock_project: models.Projects) -> None:
    mock_db.get.return_value = mock_project
    delete_project_(mock_project, mock_db)
    mock_db.delete.assert_called_once_with(mock_project)
    mock_db.commit.assert_called_once()
