from fastapi import APIRouter

from app.api.v1.events import router as events_router
from app.api.v1.memories import router as memories_router
from app.api.v1.graph import router as graph_router
from app.api.v1.messages import router as message_router

router = APIRouter()
router.include_router(events_router)
router.include_router(memories_router)
router.include_router(graph_router)
router.include_router(message_router)