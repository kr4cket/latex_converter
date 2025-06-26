from app.infra.queue.app import celery_app
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.settings import settings
from app.infra.database.models import Conversions, StatusEnum
from app.converter.service import Converter

sync_db_url = settings.db_settings.db_url.replace("+asyncpg", "")
engine     = create_engine(sync_db_url, echo=False)
SyncSession = sessionmaker(engine, autoflush=False, autocommit=False)

@celery_app.task(
    name="convert_pdf_task",
    acks_late=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 10},
)
def convert_pdf_task(conversion_id: int, input_path: str, filename: str):
    session = SyncSession()
    service = Converter()
    try:
        conv = session.get(Conversions, conversion_id)
        conv.status     = StatusEnum.processing
        conv.started_at = datetime.utcnow()
        session.commit()

        service.convert_pdf(Path(input_path))
        service.save(Path(input_path), conv.file_id)
        service.cleanup(Path(input_path), Path(input_path).suffix)

        conv.download_url = f"download/{conv.file_id}"
        conv.status       = StatusEnum.completed
        conv.ended_at     = datetime.utcnow()
        session.commit()

    except Exception as e:
        conv.status   = StatusEnum.failed
        conv.error    = str(e)
        conv.ended_at = datetime.utcnow()
        session.commit()
    finally:
        session.close()