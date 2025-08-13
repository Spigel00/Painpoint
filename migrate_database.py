"""
Database migration script to add missing columns to existing tables
"""
import psycopg2
from sqlalchemy import create_engine, text
import os
from pathlib import Path

def migrate_database():
    """Add missing columns to fetched_problems table"""
    
    print("🔄 Starting database migration...")
    
    # Direct database URL - same as in .env file
    DATABASE_URL = "postgresql+psycopg2://postgres:Jiraiya%40106@localhost:5432/painpoint_ai"
    
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    # SQL commands to add missing columns
    migration_sql = [
        # Add missing columns to fetched_problems table
        "ALTER TABLE fetched_problems ADD COLUMN IF NOT EXISTS source_platform VARCHAR(20) DEFAULT 'reddit'",
        "ALTER TABLE fetched_problems ADD COLUMN IF NOT EXISTS embedding_vector JSON",
        "ALTER TABLE fetched_problems ADD COLUMN IF NOT EXISTS cluster_id INTEGER REFERENCES problem_clusters(id)",
        "ALTER TABLE fetched_problems ADD COLUMN IF NOT EXISTS ai_problem_statement TEXT",
        "ALTER TABLE fetched_problems ADD COLUMN IF NOT EXISTS confidence_score REAL DEFAULT 0.0",
        "ALTER TABLE fetched_problems ADD COLUMN IF NOT EXISTS is_claimed BOOLEAN DEFAULT FALSE",
        "ALTER TABLE fetched_problems ADD COLUMN IF NOT EXISTS claim_count INTEGER DEFAULT 0",
        "ALTER TABLE fetched_problems ADD COLUMN IF NOT EXISTS solution_count INTEGER DEFAULT 0",
        "ALTER TABLE fetched_problems ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        
        # Update existing records to have default values
        "UPDATE fetched_problems SET source_platform = 'reddit' WHERE source_platform IS NULL",
        "UPDATE fetched_problems SET confidence_score = 0.0 WHERE confidence_score IS NULL",
        "UPDATE fetched_problems SET is_claimed = FALSE WHERE is_claimed IS NULL",
        "UPDATE fetched_problems SET claim_count = 0 WHERE claim_count IS NULL",
        "UPDATE fetched_problems SET solution_count = 0 WHERE solution_count IS NULL",
        "UPDATE fetched_problems SET processed_at = CURRENT_TIMESTAMP WHERE processed_at IS NULL",
    ]
    
    try:
        with engine.connect() as conn:
            for sql in migration_sql:
                try:
                    print(f"  Executing: {sql}")
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"  ✅ Success")
                except Exception as e:
                    print(f"  ⚠️  {sql} - {str(e)}")
                    continue
                    
        print("✅ Database migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    migrate_database()
