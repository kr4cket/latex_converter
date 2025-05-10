from fastapi import APIRouter

from app.api.v1.enpoints import converter

router = APIRouter()
router.include_router(converter.router)
