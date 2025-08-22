-- app/dash_assistant/migrations/004_use_superset_id_as_key.sql
-- Change primary key from dashboard_slug to superset_id

-- Drop existing unique constraint on dashboard_slug
DROP INDEX IF EXISTS uq_bi_entity_slug;

-- Add unique constraint on superset_id (should be unique for dashboards)
-- Check if constraint already exists before adding
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uq_bi_entity_superset_id'
    ) THEN
        ALTER TABLE bi_entity 
        ADD CONSTRAINT uq_bi_entity_superset_id UNIQUE (superset_id);
    END IF;
END $$;

-- Update any existing URLs to use the new format
UPDATE bi_entity 
SET url = 'https://superset.walletteam.org/superset/dashboard/' || superset_id
WHERE entity_type = 'dashboard' AND superset_id IS NOT NULL;

-- Make dashboard_slug nullable since we're not using it as primary key anymore
ALTER TABLE bi_entity 
ALTER COLUMN dashboard_slug DROP NOT NULL;

COMMENT ON CONSTRAINT uq_bi_entity_superset_id ON bi_entity IS 'Unique constraint on superset_id for dashboards and charts';
