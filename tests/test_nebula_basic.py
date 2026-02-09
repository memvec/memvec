from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient


def _kg_tests_enabled() -> bool:
    return os.getenv('RUN_KG_TESTS', 'false').lower() in ('1', 'true', 'yes')


pytestmark = pytest.mark.skipif(
    not _kg_tests_enabled(),
    reason='Set RUN_KG_TESTS=true to run NebulaGraph integration tests',
)


def test_nebula_upsert_on_memory_create(app_client: TestClient) -> None:
    r = app_client.post(
        '/v1/memories',
        json={
            'type': 'preference',
            'scope': 'profile',
            'key': 'response_verbosity',
            'value': {'style': 'concise', 'mentions': 'fastapi qdrant'},
            'confidence': 0.95,
        },
    )
    assert r.status_code == 200, r.text
    mem_id = r.json()['id']

    node_id = f'memory:{mem_id}'
    n = app_client.get(f'/v1/graph/nodes/{node_id}')
    assert n.status_code == 200, n.text
