from sqlalchemy import text


def apply_compatibility_migrations(engine):
    """Add new auth/profile columns to existing PostgreSQL development databases."""
    if engine.dialect.name != "postgresql":
        return
    statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS institution VARCHAR(200)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS department VARCHAR(150)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS research_interests JSON NOT NULL DEFAULT '[]'::json",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS skills JSON NOT NULL DEFAULT '[]'::json",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_picture VARCHAR(500)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS approval_status VARCHAR(20) NOT NULL DEFAULT 'Approved'",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN NOT NULL DEFAULT TRUE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_code_hash VARCHAR(128)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_code_expires_at TIMESTAMPTZ",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_code_sent_at TIMESTAMPTZ",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_attempts INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_code_hash VARCHAR(128)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_code_expires_at TIMESTAMPTZ",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_code_sent_at TIMESTAMPTZ",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_attempts INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE publications ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'Draft'",
        "ALTER TABLE publications ADD COLUMN IF NOT EXISTS document_path VARCHAR(500)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        "ALTER TABLE researchers ADD COLUMN IF NOT EXISTS user_id INTEGER",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS institution_id INTEGER",
        "ALTER TABLE researchers ADD COLUMN IF NOT EXISTS institution_id INTEGER",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_researchers_user_id ON researchers (user_id)",
        "CREATE INDEX IF NOT EXISTS ix_users_institution_id ON users (institution_id)",
        "CREATE INDEX IF NOT EXISTS ix_researchers_institution_id ON researchers (institution_id)",
        "ALTER TABLE researchers ADD COLUMN IF NOT EXISTS source VARCHAR(60)",
        "ALTER TABLE researchers ADD COLUMN IF NOT EXISTS source_id VARCHAR(120)",
        "ALTER TABLE researchers ADD COLUMN IF NOT EXISTS source_url VARCHAR(500)",
        "ALTER TABLE institutions ADD COLUMN IF NOT EXISTS source VARCHAR(60)",
        "ALTER TABLE institutions ADD COLUMN IF NOT EXISTS source_id VARCHAR(120)",
        "ALTER TABLE institutions ADD COLUMN IF NOT EXISTS source_url VARCHAR(500)",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_researchers_source_id ON researchers (source_id) WHERE source_id IS NOT NULL",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_institutions_source_id ON institutions (source_id) WHERE source_id IS NOT NULL",
        "CREATE INDEX IF NOT EXISTS ix_users_email_verified ON users (email_verified)",
        "UPDATE users SET role = 'Researcher' WHERE role = 'User'",
    ]
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
        connection.execute(text("""
            DO $$ BEGIN
              IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_researchers_user_id') THEN
                ALTER TABLE researchers ADD CONSTRAINT fk_researchers_user_id FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
              END IF;
            END $$;
        """))
        connection.execute(text("""
            DO $$ BEGIN
              IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_users_institution_id') THEN
                ALTER TABLE users ADD CONSTRAINT fk_users_institution_id FOREIGN KEY (institution_id) REFERENCES institutions(id) ON DELETE SET NULL;
              END IF;
              IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_researchers_institution_id') THEN
                ALTER TABLE researchers ADD CONSTRAINT fk_researchers_institution_id FOREIGN KEY (institution_id) REFERENCES institutions(id) ON DELETE SET NULL;
              END IF;
            END $$;
        """))
        connection.execute(text("UPDATE users SET institution_id = institutions.id FROM institutions WHERE users.institution_id IS NULL AND LOWER(users.institution) = LOWER(institutions.name)"))
        connection.execute(text("UPDATE researchers SET institution_id = institutions.id FROM institutions WHERE researchers.institution_id IS NULL AND LOWER(researchers.institution) = LOWER(institutions.name)"))
