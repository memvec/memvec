from __future__ import annotations

import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app


def _qdrant_tests_enabled() -> bool:
    return os.getenv('RUN_QDRANT_TESTS', 'true').lower() in ('1', 'true', 'yes')


pytestmark = pytest.mark.skipif(
    not _qdrant_tests_enabled(),
    reason='Set RUN_QDRANT_TESTS=true to run real Qdrant integration tests.',
)


@pytest.fixture()
def app_client() -> Generator[TestClient, None, None]:
    # use in-memory DB; Qdrant is real.
    engine = create_engine(
        'sqlite+pysqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_memory_is_persisted_in_qdrant(app_client: TestClient) -> None:
    # Create memory via API (this should upsert to Qdrant).
    r = app_client.post(
        '/v1/memories',
        json={
            'type': 'preference',
            'scope': 'profile',
            'key': 'response_verbosity',
            'value': {'style': 'concise'},
            'confidence': 0.95,
        },
    )
    assert r.status_code == 200, r.text
    mem = r.json()
    mem_id = int(mem['id'])

    # Verify in Qdrant
    qc = QdrantClient(url=settings.qdrant_url)
    points = qc.retrieve(collection_name=settings.qdrant_collection, ids=[mem_id])
    assert len(points) == 1

    payload = points[0].payload or {}
    assert payload.get('type') == 'preference'
    assert payload.get('scope') == 'profile'
    assert payload.get('key') == 'response_verbosity'
    assert payload.get('value') == {'style': 'concise'}
