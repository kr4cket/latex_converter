from fastapi import APIRouter
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse
import os
from pathlib import Path
import uuid

from app.converter.service import Converter, service

router = APIRouter()

TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)


@router.post("/convert")
async def convert_file(file: UploadFile = File(...)):
    try:
        file_id = uuid.uuid4()
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{file_id}{file_extension}"
        file_path = TEMP_DIR / unique_filename

        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # TODO: вынести в очередь задач!
        service.convert_pdf(file_path)
        service.save(file_path, file_id)
        service.cleanup(file_path, file_extension)

        file_info = {
            "description": "Data converted!",
            "download_url": router.url_path_for("download_pdf", file_id=file_id)
        }
        return JSONResponse(status_code=201, content=file_info)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error converting file: {e}"
        )


@router.get("/convert/{file_id}")
async def download_pdf(file_id: str):
    try:
        path = service.get_download_path(file_id)
        return FileResponse(
            path=path,
            filename=f"converted_data.zip",
            media_type="application/zip"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {e}"
        )
