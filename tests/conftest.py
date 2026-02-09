from __future__ import annotations

import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import create_app


def _mysql_test_url() -> str:
    url = os.getenv('MYSQL_TEST_URL', '').strip()
    if not url:
        raise RuntimeError('MYSQL_TEST_URL is not set')

    # I add a simple guard so we don’t accidentally point at prod.
    if 'test' not in url.lower():
        raise RuntimeError("Refusing to run: MYSQL_TEST_URL must contain 'test' (safety guard)")

    return url


@pytest.fixture(scope='session')
def mysql_engine():
    engine = create_engine(_mysql_test_url(), pool_pre_ping=True)

    # I reset schema once per test session.
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    return engine


@pytest.fixture()
def db_session(mysql_engine) -> Generator[Session, None, None]:
    TestingSessionLocal = sessionmaker(bind=mysql_engine, autoflush=False, autocommit=False)
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    finally:
        db.close()


@pytest.fixture()
def app_client(db_session: Session) -> Generator[TestClient, None, None]:
    app = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        # I reuse the same session for the whole request lifecycle in this test.
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
