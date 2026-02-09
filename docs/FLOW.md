# Incoming Message → Memory Pipeline (End-to-End Flow)

This document describes what happens when an incoming message is received by the system and how it flows through persistence, qualification, vector storage, and knowledge graph updates.

---

## 1. Event Intake (API Layer)

**What happens**  
An incoming message is received via HTTP.

**Where**  
- `app/api/v1/events.py`
- Function: `create_event()`

**Details**  
- Handles `POST /v1/events`
- Accepts actor metadata, text, and optional payload

---

## 2. Event Validation (Schema Layer)

**What happens**  
Request payload is validated and parsed.

**Where**  
- `app/schemas/event.py`
- Schema: `EventCreate`

---

## 3. Event Persistence (SQL)

**What happens**  
The event is written to the relational database.

**Where**  
- `app/services/event_service.py`
- Function: `create_event()`

**Details**  
- `db.add(event)`
- `db.commit()`
- `db.refresh(event)`

---

## 4. Automatic Memory Processing Trigger

**What happens**  
Once the event is stored, the system attempts to convert it into memories.

**Where**  
- `app/api/v1/events.py`
- Function: `create_event()`
- Calls: `memory_svc.process_event_to_memories()`

---

## 5. LLM Prompt Construction

**What happens**  
A structured prompt is built from the event content.

**Where**  
- `app/integrations/llm/prompt.py`
- Function: `build_memory_qualifier_user_prompt()`

---

## 6. LLM Invocation (Qualification)

**What happens**  
The LLM (Qwen via Ollama) is invoked to decide if the event qualifies as memory.

**Where**  
- `app/integrations/llm/ollama_client.py`
- Function: `OllamaClient.generate_json()`

---

## 7. LLM Output Validation

**What happens**  
The LLM’s JSON output is validated against a strict schema.

**Where**  
- `app/schemas/llm.py`
- Schema: `MemoryQualification`
- `app/services/memory_service.py`
- Function: `process_event_to_memories()`

**Outcome**  
- Invalid or malformed output → fail closed (no memory stored)

---

## 8. Memory Qualification Decision

**What happens**  
The system decides whether to store a memory.

**Where**  
- `app/services/memory_service.py`
- Function: `process_event_to_memories()`

**Rules**  
- `is_memory = false` → stop
- `is_memory = true` → continue

---

## 9. Memory Persistence (SQL)

**What happens**  
A memory record is created and stored.

**Where**  
- `app/models/memory.py`
- Model: `Memory`
- `app/services/memory_service.py`
- Function: `process_event_to_memories()`

---

## 10. Vector Embedding Generation

**What happens**  
The memory content is converted into an embedding.

**Where**  
- `app/integrations/vector/embedder.py`
- Class: `SentenceTransformerEmbedder`
- Method: `embed()`
- Called from: `MemoryService._vdb_upsert_memory()`

---

## 11. Vector DB Persistence (Qdrant)

**What happens**  
The embedding is stored in Qdrant for semantic search.

**Where**  
- `app/integrations/vector/qdrant_db.py`
- Method: `QdrantVectorDB.upsert()`
- Called from: `MemoryService._vdb_upsert_memory()`

**Details**  
- Point ID = `memory.id`
- Payload includes type, scope, key, value, confidence

---

## 12. Knowledge Graph Upsert (NebulaGraph)

**What happens**  
Graph nodes and edges are created/updated.

**Where**  
- `app/services/kg_service.py`
- Function: `KGService.upsert_memory()`
- `app/integrations/kg/nebula_graph.py`
- Functions: `upsert_node()`, `upsert_edge()`

**Graph Actions**  
- Create/Update `Memory` vertex  
- Optionally create `Actor` vertex  
- Create edges:
  - `Actor → HAS_MEMORY → Memory`
  - `Memory → ABOUT → Entity`

---

## 13. API Response

**What happens**  
The API returns the created Event.

**Where**  
- `app/api/v1/events.py`
- Function: `create_event()`

**Note**  
Memory creation is a side effect; the event response is returned synchronously.

---

## Summary

This design keeps:
- SQL as the source of truth
- Vector DB for semantic recall
- Knowledge Graph for relational reasoning and explainability