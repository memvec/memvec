from dotenv import load_dotenv
load_dotenv() 

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import router as v1_router
from app.core.logging_config import setup_logging
from app.db.base import Base
from app.db.session import engine

import app.models

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    # auto-create tables for now. TODO move to Alembic once schema stabilizes.
    Base.metadata.create_all(bind=engine)

    yield

    # shutdown
    # (nothing for now)


def create_app() -> FastAPI:
    app = FastAPI(title='mem-vec', lifespan=lifespan)
    app.include_router(v1_router)
    return app


app = create_app()
