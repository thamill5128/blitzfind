#!/usr/bin/env python3
"""
Script to ensure database indexes are properly created for optimal performance
"""

from sqlalchemy import create_engine, text, inspect
import os

def ensure_indexes():
    """Ensure all necessary indexes exist for optimal query performance"""
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./blitzfind.db")
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
    
    with engine.connect() as conn:
        # Check if we're using SQLite or PostgreSQL
        is_sqlite = DATABASE_URL.startswith("sqlite")
        
        if is_sqlite:
            # SQLite-specific index creation
            # Check existing indexes
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='index'"))
            existing_indexes = [row[0] for row in result]
            
            # Create index on id column if not exists (should already exist as primary key)
            if 'ix_key_value_store_id' not in existing_indexes:
                print("Creating index on id column...")
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_key_value_store_id ON key_value_store(id)"))
                conn.commit()
            
            # Create index on created_at for potential time-based queries
            if 'ix_key_value_store_created_at' not in existing_indexes:
                print("Creating index on created_at column...")
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_key_value_store_created_at ON key_value_store(created_at)"))
                conn.commit()
                
            # Create index on updated_at for potential time-based queries
            if 'ix_key_value_store_updated_at' not in existing_indexes:
                print("Creating index on updated_at column...")
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_key_value_store_updated_at ON key_value_store(updated_at)"))
                conn.commit()
            
            # Enable SQLite optimizations
            conn.execute(text("PRAGMA journal_mode=WAL"))  # Write-Ahead Logging for better concurrency
            conn.execute(text("PRAGMA synchronous=NORMAL"))  # Faster writes
            conn.execute(text("PRAGMA cache_size=10000"))  # Larger cache
            conn.execute(text("PRAGMA temp_store=MEMORY"))  # Use memory for temp tables
            conn.commit()
            
        else:
            # PostgreSQL-specific optimizations
            # Create indexes if they don't exist
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_key_value_store_id ON key_value_store(id);
                CREATE INDEX IF NOT EXISTS idx_key_value_store_created_at ON key_value_store(created_at);
                CREATE INDEX IF NOT EXISTS idx_key_value_store_updated_at ON key_value_store(updated_at);
            """))
            conn.commit()
        
        print("Database indexes and optimizations applied successfully!")

if __name__ == "__main__":
    ensure_indexes()