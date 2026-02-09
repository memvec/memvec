-- Schema fors application (MySQL)... in case you want to create from script instead of ORM migrations.

CREATE TABLE IF NOT EXISTS memories (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,

  type VARCHAR(32) NOT NULL,
  scope VARCHAR(32) NOT NULL,
  `key` VARCHAR(128) NOT NULL,
  value JSON NOT NULL,
  confidence DOUBLE NOT NULL DEFAULT 0.0,

  assertion_count INT NOT NULL DEFAULT 0,
  decay DOUBLE NOT NULL DEFAULT 0.0,

  superseded_by_memory_id BIGINT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT fk_memories_superseded_by
    FOREIGN KEY (superseded_by_memory_id) REFERENCES memories(id)
    ON DELETE SET NULL,

  INDEX idx_memories_type_scope (type, scope),
  INDEX idx_memories_key (`key`),
  INDEX idx_memories_superseded_by (superseded_by_memory_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS events (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,

  actor_type VARCHAR(50) NOT NULL DEFAULT 'user',
  actor_id VARCHAR(128) NOT NULL DEFAULT 'unknown',
  text TEXT NULL,
  payload JSON NULL,

  memory_id BIGINT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT fk_events_memory
    FOREIGN KEY (memory_id) REFERENCES memories(id)
    ON DELETE SET NULL,

  INDEX idx_events_actor (actor_type, actor_id),
  INDEX idx_events_created_at (created_at),
  INDEX idx_events_memory_id (memory_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
