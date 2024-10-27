import aiofiles
import os
from fastapi import UploadFile
from typing import List
import magic
import uuid
from ..database.models import DBFile
from sqlalchemy.orm import Session

class FileService:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = upload_dir
        os.makedirs(upload_dir, exist_ok=True)

    async def save_file(self, file: UploadFile, user_id: str, db: Session) -> DBFile:
        # Generate unique filename
        file_id = str(uuid.uuid4())
        extension = os.path.splitext(file.filename)[1]
        filename = f"{file_id}{extension}"
        file_path = os.path.join(self.upload_dir, filename)

        # Save file
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)

        # Detect mime type
        mime_type = magic.from_file(file_path, mime=True)

        # Create database entry
        db_file = DBFile(
            id=file_id,
            user_id=user_id,
            filename=file.filename,
            file_path=file_path,
            mime_type=mime_type,
            size=os.path.getsize(file_path),
            metadata={}
        )

        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        return db_file

    async def get_user_files(self, user_id: str, db: Session) -> List[DBFile]:
        return db.query(DBFile).filter(DBFile.user_id == user_id).all()

    async def delete_file(self, file_id: str, user_id: str, db: Session) -> bool:
        file = db.query(DBFile).filter(
            DBFile.id == file_id,
            DBFile.user_id == user_id
        ).first()

        if not file:
            return False

        # Delete physical file
        try:
            os.remove(file.file_path)
        except OSError:
            pass

        # Delete database entry
        db.delete(file)
        db.commit()

        return True