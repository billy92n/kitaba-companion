ALTER TABLE campaigns ADD COLUMN death_pending INTEGER NOT NULL DEFAULT 0 CHECK (death_pending IN (0,1));
ALTER TABLE campaigns ADD COLUMN death_summary TEXT;
