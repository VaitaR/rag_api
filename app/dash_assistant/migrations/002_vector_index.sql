-- app/dash_assistant/migrations/002_vector_index.sql
-- Create vector index and optimize for mass loading

-- Skip vector index creation for now due to pgvector version limitations
-- Will create index after fixing vector dimension
-- CREATE INDEX IF NOT EXISTS idx_bi_chunk_emb_ivfflat
-- ON bi_chunk USING ivfflat (embedding vector_cosine_ops) 
-- WITH (lists = 100);

-- Create function to analyze tables after mass loading
CREATE OR REPLACE FUNCTION analyze_dash_assistant_tables()
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    -- Analyze all dash assistant tables to update statistics
    -- This is critical for query performance after mass data loading
    ANALYZE bi_entity;
    ANALYZE bi_chart;
    ANALYZE bi_chunk;
    ANALYZE term_dict;
    ANALYZE query_log;
    
    -- Log the analysis
    RAISE NOTICE 'Analyzed all dash assistant tables for optimal query performance';
END$$;

-- Create function to optimize vector index after mass loading
CREATE OR REPLACE FUNCTION optimize_vector_index()
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    -- Skip reindexing for now due to pgvector limitations
    -- REINDEX INDEX idx_bi_chunk_emb_ivfflat;
    
    -- Analyze the chunk table specifically for vector operations
    ANALYZE bi_chunk;
    
    RAISE NOTICE 'Analyzed chunk table (vector index optimization skipped)';
END$$;

-- Create convenience function to run full optimization
CREATE OR REPLACE FUNCTION optimize_after_mass_loading()
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    PERFORM analyze_dash_assistant_tables();
    PERFORM optimize_vector_index();
    
    RAISE NOTICE 'Full optimization completed after mass loading';
END$$;
