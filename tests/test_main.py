import hashlib
import uuid
from datetime import timedelta
from typing import Generator
from unittest import mock
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

import src.models as models
from src.auth import create_access_token
from src.main import app
from src.schemas import Project, ProjectDetails, User
from src.service import (
    add_user_to_project_,
    authenticate_user,
    create_user_,
    delete_project_,
    get_project_,
    get_session,
    get_user,
    get_user_projects,
    is_project_admin,
    update_project_details_,
)


@pytest.fixture(autouse=True)
def mock_jwt_config():
    with mock.patch.multiple(
        "src.auth",
        OAUTH_SECRET_KEY="test_secret_key",
    ):
        yield


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
def mock_user() -> Generator[models.Users]:
    yield models.Users(
        id=uuid.uuid4(), name="test@example.com", email="test@example.com", hashed_password="hashed_password"
    )


@pytest.fixture
def user_data() -> Generator[User]:
    yield User(name="Test User", email="test@example.com", password="test_password")


@pytest.fixture
def mock_token(mock_user) -> Generator[str]:
    yield create_access_token(mock_user.name, mock_user.id, timedelta(minutes=30))


@pytest.fixture
def client(override_get_db: MagicMock) -> Generator[TestClient]:
    yield TestClient(app)


def test_get_projects(
    client: TestClient, mock_db: MagicMock, mock_user: models.Users, mock_token: str, mock_project: models.Projects
) -> None:
    mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_project]
    response = client.get("/projects", headers={"Authorization": f"Bearer {mock_token}"})
    assert response.status_code == 200
    assert response.json() == [
        {
            "project_id": str(mock_project.id),
            "name": mock_project.name,
            "description": mock_project.description,
        }
    ]


def test_create_project(
    client: TestClient, mock_db: MagicMock, project_data: Project, mock_project: models.Projects, mock_token: str
) -> None:
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    headers = {"Authorization": f"Bearer {mock_token}"}
    response = client.post("/projects", json=project_data.model_dump(), headers=headers)
    response_json = response.json()
    expected_data = {
        "project_id": response_json["project_id"],
        "name": mock_project.name,
        "description": mock_project.description,
    }
    assert response.status_code == 201
    assert response_json == expected_data


def test_get_project_details_successful(
    client: TestClient, mock_token: str, mock_project: models.Projects, mock_user: models.Users, mock_db: MagicMock
):
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_project
    response = client.get(f"/project/{mock_project.id}/info", headers={"Authorization": f"Bearer {mock_token}"})

    response_json = response.json()
    expected_data = {
        "project_id": response_json["project_id"],
        "name": mock_project.name,
        "description": mock_project.description,
    }
    assert response.status_code == 200
    assert response_json == expected_data


def test_get_project_details_not_found(client: TestClient, mock_db: MagicMock, mock_token, mock_project) -> None:
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    response = client.get(f"/project/{uuid.uuid4()}/info", headers={"Authorization": f"Bearer {mock_token}"})
    assert response.status_code == 404


def test_update_project_details(client: TestClient, mock_db, mock_project, project_data, mock_user, mock_token):
    mock_project_data = mock.MagicMock()
    mock_project_data.id = mock_project.id
    mock_project_data.name = mock_project.name
    mock_project_data.description = mock_project.description
    mock_db.return_value.query.return_value.filter.return_value.first.return_value = mock_project_data
    response = client.put(
        f"/project/{mock_project.id}/info",
        json={"name": project_data.name, "description": project_data.description},
        headers={"Authorization": f"Bearer {mock_token}"},
    )
    assert response.status_code == 200


def test_update_project_details_not_found(
    client: TestClient, mock_db, mock_user, mock_token, mock_project, project_data
):
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    response = client.put(
        f"/project/{mock_project.id}/info",
        json={"name": project_data.name, "description": project_data.description},
        headers={"Authorization": f"Bearer {mock_token}"},
    )
    assert response.status_code == 404


def test_delete_project_success(
    client: TestClient, mock_db: MagicMock, mock_project: models.Projects, mock_token
) -> None:
    project_id = mock_project.id
    with patch("src.service.get_user_projects", return_value=[mock_project]):
        headers = {"Authorization": f"Bearer {mock_token}"}
        response = client.delete(f"/project/{project_id}", headers=headers)
        mock_db.query.return_value.get.return_value = mock_project
        mock_db.delete = MagicMock()
        mock_db.commit = MagicMock()
    assert response.status_code == 204
    assert response.content == b""
    mock_db.query.assert_called_once()


def test_delete_project_not_found(client: TestClient, mock_db: MagicMock, mock_token) -> None:
    project_id = uuid.uuid4()
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    with patch("src.service.get_user_projects", return_value=[None]):
        headers = {"Authorization": f"Bearer {mock_token}"}
        response = client.delete(f"/project/{project_id}", headers=headers)

    assert response.status_code == 404
    assert response.json() == {"detail": f"Project {project_id} not found"}


def test_add_user_to_project_endpoint_success(
    client: TestClient, mock_db: MagicMock, mock_token, mock_user: models.Users, mock_project: models.Projects
) -> None:
    with (
        patch("src.main.get_user") as mock_get_user,
        patch("src.main.is_project_admin", return_value=True),
        patch("src.main.get_project_", return_value=False),
        patch("src.main.add_user_to_project_"),
    ):
        invited_user = MagicMock()
        invited_user.email = "new_user@example.com"
        mock_get_user.return_value = invited_user
        response = client.post(
            f"/project/{mock_project.id}/invite",
            params={"user_email": "new_user@example.com"},
            headers={"Authorization": f"Bearer {mock_token}"},
        )

    assert response.status_code == 201


def test_add_user_to_project_endpoint_not_admin(
    client: TestClient, mock_db: MagicMock, mock_token, mock_user: models.Users, mock_project: models.Projects
) -> None:
    with (
        patch("src.main.get_user") as mock_get_user,
        patch("src.main.is_project_admin", return_value=False),
    ):
        mock_get_user.return_value = MagicMock()
        response = client.post(
            f"/project/{mock_project.id}/invite",
            params={"user_email": "new_user@example.com"},
            headers={"Authorization": f"Bearer {mock_token}"},
        )

    assert response.status_code == 403
    assert response.json() == {"detail": "Only project admins can share projects"}


def test_add_user_to_project_endpoint_user_not_found(
    client: TestClient, mock_db: MagicMock, mock_token, mock_user: models.Users, mock_project: models.Projects
) -> None:
    mock_db.query().filter(mock.ANY).one_or_none.return_value = None
    response = client.post(
        f"/project/{mock_project.id}/invite",
        params={"user_email": "nonexistent@example.com"},
        headers={"Authorization": f"Bearer {mock_token}"},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "User with email nonexistent@example.com not found"}


def test_add_user_to_project_endpoint_user_already_in_project(
    client: TestClient, mock_db: MagicMock, mock_token, mock_user: models.Users, mock_project: models.Projects
) -> None:
    with (
        patch("src.main.get_user") as mock_get_user,
        patch("src.main.is_project_admin", return_value=True),
        patch("src.main.get_project_", return_value=True),
    ):
        mock_get_user.return_value = mock_user
        response = client.post(
            f"/project/{mock_project.id}/invite",
            params={"user_email": "existing@example.com"},
            headers={"Authorization": f"Bearer {mock_token}"},
        )

    assert response.status_code == 400
    assert response.json() == {"detail": "User is already in this project"}


def test_get_project_with_user_access(
    mock_db: MagicMock, mock_project: models.Projects, mock_user: models.Users
) -> None:
    project_id = mock_project.id
    user_id = mock_user.id
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_project
    result = get_project_(mock_db, project_id, user_id)
    assert result == mock_project


def test_get_user_projects(mock_db: MagicMock, mock_project: models.Projects, mock_user: models.Users) -> None:
    user_id = mock_user.id
    mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_project]
    result = get_user_projects(mock_db, user_id)
    assert result[0] == mock_project


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


def test_create_user(mock_db: MagicMock, user_data: User) -> None:
    create_user_(mock_db, user_data)
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


def test_authenticate_user_success(mock_db: MagicMock, mock_user: models.Users) -> None:
    h = hashlib.new("SHA256")
    h.update("test_password".encode())
    password_hash = h.hexdigest()
    mock_user.hashed_password = password_hash
    mock_db.query.return_value.filter.return_value.one_or_none.return_value = mock_user
    result = authenticate_user(mock_user.email, "test_password", mock_db)

    assert result == mock_user


def test_authenticate_user_invalid_credentials(mock_db: MagicMock, mock_user: models.Users) -> None:
    h = hashlib.new("SHA256")
    h.update("test_password".encode())
    password_hash = h.hexdigest()
    mock_user.hashed_password = password_hash
    mock_db.query.return_value.filter.return_value.one_or_none.return_value = mock_user
    result = authenticate_user(mock_user.email, "wrong_password", mock_db)
    assert result is None


def test_authenticate_user_not_found(mock_db: MagicMock) -> None:
    mock_db.query.return_value.filter.return_value.first.return_value = None
    result = authenticate_user("nonexistent@example.com", "password", mock_db)

    assert result is None


def test_is_project_admin_true(mock_db: MagicMock, mock_project: models.Projects, mock_user: models.Users) -> None:
    project_id = mock_project.id
    user_id = mock_user.id
    mock_db.execute.return_value.one.return_value = True
    result = is_project_admin(mock_db, project_id, user_id)

    assert result


def test_is_project_admin_false(mock_db: MagicMock, mock_project: models.Projects, mock_user: models.Users) -> None:
    project_id = mock_project.id
    user_id = mock_user.id
    mock_db.execute.return_value.one_or_none.return_value = None
    result = is_project_admin(mock_db, project_id, user_id)

    assert not result


def test_get_user_existing_user(mock_db: MagicMock) -> None:
    mock_user = MagicMock()
    mock_db.query().filter().one_or_none.return_value = mock_user
    result = get_user("existing@example.com", mock_db)

    assert result == mock_user


def test_get_user_non_existing_user(mock_db: MagicMock) -> None:
    mock_db.query().filter().one_or_none.return_value = None
    result = get_user("nonexistent@example.com", mock_db)

    assert result is None


def test_add_user_to_project_success(mock_db: MagicMock, mock_user: models.Users) -> None:
    project_id = uuid.uuid4()
    add_user_to_project_(mock_user, project_id, mock_db)

    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
