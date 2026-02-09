from __future__ import annotations

from typing import Any

from nebula3.Config import Config
from nebula3.gclient.net import ConnectionPool

from app.core.config import settings
from app.integrations.kg.base import GraphDB


def _escape(s: str) -> str:
    # I escape quotes so simple strings don't break nGQL.
    return (s or '').replace('\\', '\\\\').replace('"', '\\"')


class NebulaGraphDB(GraphDB):
    """
    I implement GraphDB using NebulaGraph.
    Assumption: SPACE + TAGs + EDGEs already exist (see scripts/nebula_schema.ngql).
    """

    def __init__(self) -> None:
        cfg = Config()
        cfg.max_connection_pool_size = 10

        self.pool = ConnectionPool()
        ok = self.pool.init([(settings.nebula_host, settings.nebula_port)], cfg)
        if not ok:
            raise RuntimeError('Failed to init Nebula connection pool')

        self.space = settings.nebula_space

    def _exec(self, ngql: str) -> None:
        sess = self.pool.get_session(settings.nebula_user, settings.nebula_password)
        try:
            r = sess.execute(f'USE {self.space};')
            if not r.is_succeeded():
                raise RuntimeError(f'Nebula USE failed: {r.error_msg()}')

            r = sess.execute(ngql)
            if not r.is_succeeded():
                raise RuntimeError(f'Nebula query failed: {r.error_msg()} | ngql={ngql}')
        finally:
            sess.release()

    def upsert_node(self, node_id: str, label: str, props: dict[str, Any]) -> None:
        vid = _escape(node_id)

        if label == 'Actor':
            actor_type = _escape(str(props.get('actor_type', '')))
            actor_id = _escape(str(props.get('actor_id', '')))
            ngql = f'UPSERT VERTEX ON Actor "{vid}" SET actor_type="{actor_type}", actor_id="{actor_id}";'
            self._exec(ngql)
            return

        if label == 'Memory':
            memory_id = int(props.get('memory_id') or 0)
            mtype = _escape(str(props.get('type', '')))
            scope = _escape(str(props.get('scope', '')))
            key = _escape(str(props.get('key', '')))
            conf = float(props.get('confidence') or 0.0)
            ngql = (
                f'UPSERT VERTEX ON Memory "{vid}" '
                f'SET memory_id={memory_id}, type="{mtype}", scope="{scope}", key="{key}", confidence={conf};'
            )
            self._exec(ngql)
            return

        if label == 'Entity':
            name = _escape(str(props.get('name', '')))
            entity_type = _escape(str(props.get('entity_type', '')))
            ngql = f'UPSERT VERTEX ON Entity "{vid}" SET name="{name}", entity_type="{entity_type}";'
            self._exec(ngql)
            return

        raise ValueError(f'Unknown label: {label}')

    def upsert_edge(self, src_id: str, edge_type: str, dst_id: str, props: dict[str, Any] | None = None) -> None:
        # I ignore props for now to keep edges simple.
        src = _escape(src_id)
        dst = _escape(dst_id)

        if edge_type not in ('HAS_MEMORY', 'ABOUT'):
            raise ValueError(f'Unknown edge_type: {edge_type}')

        ngql = f'UPSERT EDGE ON {edge_type} "{src}" -> "{dst}" SET _dummy=1;'
        # Nebula requires at least one property on UPSERT EDGE. We'll create a dummy prop.
        # We'll also need the edge schema to allow it — easiest is to define no props and use INSERT instead.
        # So I use INSERT IGNORE semantics by doing INSERT EDGE (idempotency is handled by same src/dst/rank).
        #
        # To avoid schema changes, use INSERT EDGE without props:
        ngql = f'INSERT EDGE IF NOT EXISTS {edge_type}() VALUES "{src}"->"{dst}":();'
        self._exec(ngql)

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        vid = _escape(node_id)

        ngql = f'FETCH PROP ON * "{vid}" YIELD vertex AS v;'
        sess = self.pool.get_session(settings.nebula_user, settings.nebula_password)
        try:
            r = sess.execute(f'USE {self.space};')
            if not r.is_succeeded():
                raise RuntimeError(f'Nebula USE failed: {r.error_msg()}')

            r = sess.execute(ngql)
            if not r.is_succeeded():
                raise RuntimeError(f'Nebula query failed: {r.error_msg()} | ngql={ngql}')

            if r.row_size() == 0:
                return None

            # col_names = [r.keys()[i] for i in range(r.column_size())]
            # row = r.row_values(0)
            # props: dict[str, Any] = {}
            # for i, k in enumerate(col_names):
            #     props[str(k)] = str(row[i])

            # return {'id': node_id, 'props': props}
            v = r.row_values(0)[0]
            return {'id': node_id, 'vertex': str(v)}
        finally:
            sess.release()


    def neighbors(self, node_id: str, edge_type: str | None = None) -> list[dict[str, Any]]:
        vid = _escape(node_id)
        et = edge_type or ''
        edge_clause = f'OVER {et}' if et else 'OVER HAS_MEMORY,ABOUT'

        ngql = f'GO FROM "{vid}" {edge_clause} YIELD edge AS edge, dst(edge) AS dst;'
        sess = self.pool.get_session(settings.nebula_user, settings.nebula_password)
        try:
            r = sess.execute(f'USE {self.space};')
            if not r.is_succeeded():
                raise RuntimeError(f'Nebula USE failed: {r.error_msg()}')

            r = sess.execute(ngql)
            if not r.is_succeeded():
                raise RuntimeError(f'Nebula query failed: {r.error_msg()} | ngql={ngql}')

            out: list[dict[str, Any]] = []
            for i in range(r.row_size()):
                row = r.row_values(i)
                # row[0]=edge name, row[1]=dst vid
                out.append({'edge': str(row[0]), 'dst': str(row[1])})
            return out
        finally:
            sess.release()
