# memvec

Project aiming to bould a lightweight memory storage & retrieval service (FastAPI + MySQL + Qdrant + NebulaGraph). This can be used for agentic or non-agentic AI applications. 

## Summary
memvec ingests events, qualifies them (optionally via an LLM), persists structured memories, indexes them into a vector DB (Qdrant) and upserts metadata into a knowledge graph (NebulaGraph). It is designed to be resilient when optional integrations (LLM, Qdrant, KG) are unavailable.

## Quickstart

1. Create a virtualenv and install dependencies:
   ```sh
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Configure environment:
   - Copy `.env.example` → `.env` and set:
     - DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
     - QDRANT_URL, QDRANT_API_KEY (if needed)
     - NEBULA_* (nebula graph connection settings)
     - USE_LLM_QUALIFIER (true/false)
     - Other settings in `app/core/config.py`

3. (Optional) Create MySQL schema:
   ```sh
   DB_HOST=127.0.0.1 DB_USER=root DB_PASSWORD=root python db_script/create_schema.py
   ```

4. Run the app:
   ```sh
   uvicorn app.main:app --reload
   ```

5. Run tests:
   ```sh
   pytest -q
   ```
   Integration tests that require external services are opt-in via env flags:
   - RUN_QDRANT_TESTS
   - RUN_KG_TESTS
   - RUN_LLM_TESTS

5. Docs:

   Refer to FLOW.md in docs folder for understanding the flow.
## Architecture (high level)

- HTTP API: app/api/v1 (routers)
- DB models: app/models (Event, Memory)
- Services:
  - MemoryService (app/services/memory_service.py): processes events → memories, persists to DB, upserts to Qdrant and KG.
  - EventService (app/services/event_service.py)
  - KGService (app/services/kg_service.py)
- Vector integrations:
  - QdrantVectorDB (app/integrations/vector/qdrant_db.py)
  - SentenceTransformerEmbedder (app/integrations/vector/embedder.py)
- LLM integration:
  - OllamaClient (app/integrations/llm/ollama_client.py)
  - Memory qualification prompt builders (app/integrations/llm/prompt.py)

## Memory processing behavior (concise)

- If an event has no text/payload: ignored.
- If USE_LLM_QUALIFIER is false: fallback creates a single `episode` memory with scope `session` and low confidence.
- If USE_LLM_QUALIFIER is true: the LLM is called to produce JSON qualification (MemoryQualification). For each qualified memory:
  - type, scope (default `profile`, `episode` forces `session`), key (auto-generated if blank), value, confidence are stored in the DB.
  - Memory is upserted into Qdrant with an embedding produced by SentenceTransformerEmbedder and payload containing metadata.
  - Memory is upserted into NebulaGraph (KG) via KGService.
- The system is resilient: failures in VDB/KG are logged and do not always abort the flow.

## Configuration & env vars
Key settings live in `app/core/config.py`. Important env vars:
- DATABASE_URL / DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
- QDRANT_URL, QDRANT_API_KEY
- NEBULA_HOST, NEBULA_PORT, NEBULA_USER, NEBULA_PASSWORD
- USE_LLM_QUALIFIER (true/false)
- Other service-specific timeouts and flags

## Useful files
- app/services/memory_service.py — core memory handling and upsert logic
- app/integrations/vector/* — embedding + Qdrant client
- app/integrations/llm/* — Ollama client + prompt templates
- app/integrations/kg/* — NebulaGraph client
- app/models — SQLAlchemy models (Event, Memory)
- docs/FLOW.md — flow documentation

## Tests
- Unit tests: run with pytest.
- Integration tests: enable via RUN_QDRANT_TESTS, RUN_KG_TESTS, RUN_LLM_TESTS in the environment.

## Contributing
- Open issues for bugs/feature requests.
- Follow existing style and add tests for new behavior.

## License

- MIT license