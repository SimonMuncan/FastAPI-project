import os
import uuid
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import and_, create_engine, select
from sqlalchemy.orm import Session, sessionmaker
import hashlib
from src.models import Projects, UserProject, Users
from src.schemas import Project, User

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


def get_project_(db: Session, project_id: uuid.UUID, user_id: uuid.UUID) -> Projects | None:
    query = select(Projects).join(UserProject).where(and_(Projects.id == project_id, UserProject.user_id == user_id))
    return db.execute(query).scalar_one_or_none()


def is_project_admin(db: Session, project_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    query = (
        select(Projects)
        .join(
            UserProject,
            and_(
                UserProject.project_id == Projects.id,
                UserProject.user_id == user_id,
                UserProject.is_admin.is_(True),
            ),
        )
        .where(Projects.id == project_id)
    )
    return db.execute(query).one_or_none() is not None


def create_project_(project: Project, db: Session, creator_id: uuid.UUID) -> Projects:
    new_project = Projects(name=project.name, description=project.description)
    db.add(new_project)
    db.flush()
    user_project = UserProject(project_id=new_project.id, user_id=creator_id, is_admin=True)
    db.add(user_project)
    db.commit()
    db.refresh(new_project)
    return new_project


def get_user_projects(db: Session, user_id: uuid.UUID) -> list[Projects]:
    query = select(Projects).join(UserProject).where(UserProject.user_id == user_id)
    return list(db.execute(query).scalars().all())


def update_project_details_(project: Projects, project_data: Project, db: Session) -> None:
    project = db.merge(project)
    if project_data.name:
        project.name = project_data.name
    if project_data.description:
        project.description = project_data.description
    db.commit()
    db.refresh(project)


def delete_project_(project: Projects, db: Session) -> None:
    db.query(UserProject).filter(UserProject.project_id == project.id).delete()
    db.delete(project)
    db.commit()


def hash_password(password: str) -> str:
    h = hashlib.new("SHA256")
    h.update(password.encode())
    return h.hexdigest()


def create_user_(db: Session, create_user_request: User) -> None:
    create_user_model = Users(
        id=uuid.uuid4(),
        name=create_user_request.name,
        email=create_user_request.email,
        hashed_password=hash_password(create_user_request.password),
    )
    db.add(create_user_model)
    db.commit()


def authenticate_user(username: str, password: str, db: Session) -> Users | None:
    user = get_user(username, db)
    if not user:
        return None
    if hash_password(password) != user.hashed_password:
        return None
    return user


def get_user(user_email: str, db: Session) -> Users | None:
    return db.query(Users).filter(Users.email == user_email).one_or_none()


def add_user_to_project_(user: Users, project_id: uuid.UUID, db: Session) -> None:
    user_project = UserProject(project_id=project_id, user_id=user.id, is_admin=False)
    db.add(user_project)
    db.commit()
