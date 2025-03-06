import uuid
from datetime import timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import AnyUrl
from sqlalchemy.orm import Session
from starlette import status

from src.auth import get_current_user, auth_middleware, create_access_token
from src.schemas import Project, ProjectDetails, CurrentUser, User, OAuth2TokenResponse, Document
from src.service import (
    add_user_to_project_,
    create_project_,
    delete_project_,
    get_project_,
    get_session,
    get_user,
    get_user_projects,
    is_project_admin,
    update_project_details_,
    create_user_,
    authenticate_user,
    upload_document_,
    AWS_BUCKET_NAME,
    get_documents,
    get_document_,
    update_document_,
    delete_document_,
)

app = FastAPI()
app.middleware("http")(auth_middleware)


@app.post("/auth", status_code=status.HTTP_201_CREATED)
async def create_user(create_user_request: User, db: Session = Depends(get_session)) -> None:
    create_user_(db, create_user_request)


@app.post("/token", response_model=OAuth2TokenResponse)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_session)
) -> OAuth2TokenResponse:
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Could not validate user {form_data.username}."
        )
    exp_time = timedelta(minutes=30)
    token = create_access_token(user.name, user.id, exp_time)
    return OAuth2TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=int(exp_time.total_seconds()),
        refresh_token=None,
        scope="read write",
    )


@app.get("/projects")
async def get_projects(
    db: Session = Depends(get_session), current_user: CurrentUser = Depends(get_current_user)
) -> list[ProjectDetails]:
    user_projects = get_user_projects(db, current_user.id)
    return [
        ProjectDetails(project_id=project.id, name=project.name, description=project.description)
        for project in user_projects
    ]


@app.post("/projects", status_code=201)
async def create_project(
    project: Project, db: Session = Depends(get_session), current_user: CurrentUser = Depends(get_current_user)
) -> ProjectDetails:
    new_project = create_project_(project, db, current_user.id)
    return ProjectDetails(**new_project.__dict__)


@app.get("/project/{project_id}/info")
async def get_project_details(
    project_id: uuid.UUID, db: Session = Depends(get_session), current_user: CurrentUser = Depends(get_current_user)
) -> ProjectDetails:
    project = get_project_(db, project_id, current_user.id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return ProjectDetails(**project.__dict__)


@app.put("/project/{project_id}/info")
async def update_project_details(
    project_id: uuid.UUID,
    project_data: Project,
    db: Session = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> None:
    project = get_project_(db, project_id, current_user.id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    update_project_details_(project, project_data, db)


@app.delete("/project/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID, db: Session = Depends(get_session), current_user: CurrentUser = Depends(get_current_user)
) -> None:
    user_id = current_user.id
    if not is_project_admin(db, project_id, user_id):
        raise HTTPException(status_code=403, detail="Only project admins can delete projects")
    project = get_project_(db, project_id, user_id)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    delete_project_(project, db)


@app.post("/project/{project_id}/invite", status_code=201)
async def add_user_to_project(
    project_id: uuid.UUID,
    user_email: str = Query(...),
    db: Session = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> None:
    user_to_add = get_user(user_email, db)
    if not is_project_admin(db, project_id, current_user.id):
        raise HTTPException(status_code=403, detail="Only project admins can share projects")
    if user_to_add is None:
        raise HTTPException(status_code=404, detail=f"User with email {user_email} not found")
    if get_project_(db, project_id, user_to_add.id):
        raise HTTPException(status_code=400, detail="User is already in this project")
    add_user_to_project_(user_to_add, project_id, db)


@app.post("/project/{project_id}/documents")
async def upload_document(
    project_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> Document:
    document = upload_document_(project_id, file, db)
    return Document(
        document_id=document.id,
        title=document.title,
        file_path=AnyUrl(f"https://{AWS_BUCKET_NAME}.s3.amazonaws.com/{document.file_path}"),
    )


@app.get("/project/{project_id}/documents")
def get_project_documents(
    project_id: uuid.UUID,
    db: Session = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> list[Document]:
    documents = get_documents(project_id, db)
    return [
        Document(
            document_id=document.id,
            title=document.title,
            file_path=AnyUrl(f"https://{AWS_BUCKET_NAME}.s3.amazonaws.com/{document.file_path}"),
        )
        for document in documents
    ]


@app.get("/document/{document_id}")
def get_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> Document:
    document = get_document_(document_id, db)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document not {document_id} found")
    return Document(
        document_id=document.id,
        title=document.title,
        file_path=AnyUrl(f"https://{AWS_BUCKET_NAME}.s3.amazonaws.com/{document.file_path}"),
    )


@app.put("/document/{document_id}", status_code=201)
def update_document(
    document_id: uuid.UUID,
    new_title: str,
    db: Session = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> None:
    document = get_document_(document_id, db)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document not {document_id} found")
    update_document_(document, new_title, db)


@app.delete("/document/{document_id}", status_code=204)
def delete_document(
    document_id: uuid.UUID,
    db: Session = Depends(get_session),
    current_user: CurrentUser = Depends(get_current_user),
) -> None:
    document = get_document_(document_id, db)
    if not document:
        raise HTTPException(status_code=404, detail=f"Document not {document_id} found")
    delete_document_(document, db)
