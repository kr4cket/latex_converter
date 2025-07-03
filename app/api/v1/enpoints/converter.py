import os
import uuid
from pathlib import Path
from typing import Literal, List, Optional

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Query
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from celery import Celery

from app.converter.service import get_download_path
from app.infra.database.database import Database
from app.infra.database.models import Conversions, StatusEnum

router = APIRouter()
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

async def get_db() -> AsyncSession:
    async with Database().get_session() as session:
        yield session

celery_client = Celery (
    "conversion_client",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1"),
)

@router.post("/convert", status_code=status.HTTP_202_ACCEPTED)
async def enqueue_convert(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    file_id   = str(uuid.uuid4())
    ext       = Path(file.filename).suffix
    out_path  = TEMP_DIR / f"{file_id}{ext}"
    content   = await file.read()
    out_path.write_bytes(content)

    conv = Conversions(
        file_id   = file_id,
        file_name = file.filename,
        status    = StatusEnum.pending,
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)

    celery_client.send_task(
        name="convert_pdf_task",
        args=[conv.id, str(out_path), file_id],
    )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "message":    "Задача поставлена в очередь",
            "task_id":    file_id,
            "status_url": router.url_path_for("get_status", file_id=file_id),
        },
    )

@router.get("/convert/status/{file_id}", name="get_status")
async def get_status(
    file_id: str,
    db: AsyncSession = Depends(get_db),
):
    q = await db.execute(select(Conversions).where(Conversions.file_id == file_id))
    conv = q.scalars().first()
    if not conv:
        raise HTTPException(status_code=404, detail="Задача не найдена")

    resp = {
        "file_id":    conv.file_id,
        "status":     conv.status.value,
        "created_at": conv.created_at.isoformat(),
    }
    if conv.status == StatusEnum.completed:
        resp["download_url"] = conv.download_url
    elif conv.status == StatusEnum.failed:
        resp["error"] = conv.error
    return resp

@router.get("/download/{file_id}", name="download")
async def download(
    file_id: str,
    db: AsyncSession = Depends(get_db),
):
    q = await db.execute(select(Conversions).where(Conversions.file_id == file_id))
    conv = q.scalars().first()
    if not conv or conv.status != StatusEnum.completed:
        raise HTTPException(status_code=404, detail="Файл не готов")
    path = get_download_path(file_id)
    return FileResponse(
        path=path,
        filename=f"{conv.file_id}.zip",
        media_type="application/zip"
    )


@router.get("/convert", name="list_conversions")
async def list_conversions(
    status: Literal["all", "pending", "processing", "completed", "failed"] = Query(
        "all", description="Фильтрация по статусу"
    ),
    file_name: Optional[str] = Query(
        None, description="Фильтрация по части имени файла (case-insensitive)"
    ),
    db: AsyncSession = Depends(get_db),
):
    query = select(Conversions)

    if status != "all":
        try:
            status_enum = StatusEnum[status]
        except KeyError:
            raise HTTPException(status_code=400, detail="Некорректный статус")
        query = query.where(Conversions.status == status_enum)

    if file_name:
        query = query.where(Conversions.file_name.ilike(f"%{file_name}%"))

    result = await db.execute(query)
    conversions: List[Conversions] = result.scalars().all()

    return [
        {
            "file_id":      conv.file_id,
            "file_name":    conv.file_name,
            "status":       conv.status.value,
            "created_at":   conv.created_at.isoformat(),
            "download_url": conv.download_url if conv.status == StatusEnum.completed else None,
            "error":        conv.error if conv.status == StatusEnum.failed else None,
        }
        for conv in conversions
    ]