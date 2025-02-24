import uuid
import pytest
from unittest.mock import MagicMock

from src.main import get_project, create_project_, get_projects_, update_project_details_, delete_project_
from src.schemas import ProjectDetails, Project
import src.models as models
from typing import Generator


@pytest.fixture
def mock_db() -> Generator[MagicMock]:
    db: MagicMock = MagicMock()
    yield db


@pytest.fixture
def project_id() -> Generator[uuid.UUID]:
    yield uuid.uuid4()


@pytest.fixture
def mock_project(project_id: uuid.UUID) -> Generator[models.Projects]:
    yield models.Projects(id=project_id, name="Test Project", description="Test Description")


@pytest.fixture
def mock_project_2(project_id: uuid.UUID) -> Generator[ProjectDetails]:
    yield ProjectDetails(project_id=project_id, name="Test Project", description="Test Description")


@pytest.fixture
def project_data() -> Generator[Project]:
    yield Project(name="Test Project", description="Test Description")


def test_get_project(
    mock_db: MagicMock, project_id: uuid.UUID, mock_project: models.Projects, mock_project_2: ProjectDetails
) -> None:
    mock_db.query.return_value.get.return_value = mock_project
    result: ProjectDetails = get_project(project_id, mock_db)
    assert result == ProjectDetails(
        project_id=mock_project_2.project_id, name=mock_project_2.name, description=mock_project_2.description
    )


def test_get_projects(mock_db: MagicMock, mock_project: models.Projects, project_id: uuid.UUID) -> None:
    mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_project]
    result: list[ProjectDetails] = get_projects_(mock_db)
    expected_result = [
        ProjectDetails(
            project_id=uuid.UUID(str(mock_project.id)),
            name=str(mock_project.name),
            description=str(mock_project.description),
        )
    ]
    assert result == expected_result


def test_create_project(mock_db: MagicMock, project_data: Project) -> None:
    models.Projects(id=uuid.uuid4(), name=project_data.name, description=project_data.description)
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.side_effect = lambda obj: obj

    result: ProjectDetails = create_project_(project_data, mock_db)
    expected_result = ProjectDetails(
        project_id=result.project_id, name=project_data.name, description=project_data.description
    )
    assert result == expected_result


def test_update_project_details(mock_db: MagicMock, project_id: uuid.UUID) -> None:
    mock_project_details: ProjectDetails = ProjectDetails(
        project_id=project_id, name="Old Name", description="Old Description"
    )
    project_data: Project = Project(name="New Name", description="New Description")

    result: ProjectDetails = update_project_details_(mock_project_details, project_data, mock_db)
    expected_result = ProjectDetails(
        project_id=mock_project_details.project_id, name=project_data.name, description=project_data.description
    )
    assert result == expected_result


def test_delete_project(mock_db: MagicMock, project_id: uuid.UUID) -> None:
    mock_project_details: ProjectDetails = ProjectDetails(
        project_id=project_id, name="Test Project", description="Test Description"
    )
    result: ProjectDetails = delete_project_(mock_project_details, mock_db)
    assert result == mock_project_details
