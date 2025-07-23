CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE embeddings (
  id SERIAL PRIMARY KEY,
  content TEXT,
  source_type TEXT,
  embedding VECTOR(1024)
);
