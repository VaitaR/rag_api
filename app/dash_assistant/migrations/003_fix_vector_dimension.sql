-- app/dash_assistant/migrations/003_fix_vector_dimension.sql
-- Fix vector dimension from 3072 to 1536 for compatibility with pgvector 0.5.1

-- Drop existing vector column and recreate with correct dimension
ALTER TABLE bi_chunk DROP COLUMN IF EXISTS embedding;
ALTER TABLE bi_chunk ADD COLUMN embedding vector(1536);
