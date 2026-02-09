from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.v1.events import memory_svc  # I reuse the singleton so it shares KG client


router = APIRouter(prefix='/v1/graph', tags=['graph'])


@router.get('/nodes/{node_id}')
def get_node(node_id: str):
    n = memory_svc.kg.graph.get_node(node_id)
    if not n:
        raise HTTPException(status_code=404, detail='node not found')
    return n


@router.get('/neighbors/{node_id}')
def neighbors(node_id: str, edge_type: str | None = None):
    return memory_svc.kg.graph.neighbors(node_id, edge_type=edge_type)
