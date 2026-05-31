from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import encrypt_file, decrypt_file
from app.models.user import User
from app.models.file import File as FileModel
from app.schemas.file import FileResponse
import uuid, os

router = APIRouter(prefix="/files", tags=["Files"])

STORAGE_PATH = "storage"

@router.post("/upload", response_model=FileResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    data = await file.read()
    encrypted = encrypt_file(data)

    filename = f"{uuid.uuid4().hex}.enc"
    filepath = os.path.join(STORAGE_PATH, filename)

    os.makedirs(STORAGE_PATH, exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(encrypted)

    db_file = FileModel(
        filename=filename,
        original_name=file.filename,
        file_size=len(data),
        mime_type=file.content_type,
        storage_path=filepath,
        is_encrypted=True,
        owner_id=current_user.id
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

@router.get("/", response_model=list[FileResponse])
def list_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(FileModel).filter(
        FileModel.owner_id == current_user.id
    ).all()

@router.get("/download/{file_id}")
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_file = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.owner_id == current_user.id
    ).first()

    if not db_file:
        raise HTTPException(404, "File not found")

    with open(db_file.storage_path, "rb") as f:
        encrypted = f.read()

    decrypted = decrypt_file(encrypted)

    return Response(
        content=decrypted,
        media_type=db_file.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={db_file.original_name}"
        }
    )

@router.delete("/{file_id}")
def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_file = db.query(FileModel).filter(
        FileModel.id == file_id,
        FileModel.owner_id == current_user.id
    ).first()

    if not db_file:
        raise HTTPException(404, "File not found")

    if os.path.exists(db_file.storage_path):
        os.remove(db_file.storage_path)

    db.delete(db_file)
    db.commit()
    return {"message": "File deleted successfully"}