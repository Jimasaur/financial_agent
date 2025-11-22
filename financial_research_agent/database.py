"""
Database module for storing financial research history.
Uses PostgreSQL to persist search queries and results.
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor


class ResearchDatabase:
    """Manages storage and retrieval of research history."""
    
    def __init__(self):
        """Initialize database connection."""
        self.conn = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Connect to PostgreSQL database."""
        try:
            database_url = os.getenv('DATABASE_URL')
            
            if not database_url:
                # Default local PostgreSQL connection
                self.conn = psycopg2.connect(
                    host=os.getenv('DB_HOST', 'localhost'),
                    port=os.getenv('DB_PORT', '5432'),
                    database=os.getenv('DB_NAME', 'financial_research'),
                    user=os.getenv('DB_USER', 'postgres'),
                    password=os.getenv('DB_PASSWORD', 'postgres')
                )
            else:
                # Use DATABASE_URL (for Heroku, Railway, etc.)
                self.conn = psycopg2.connect(database_url)
            
            self.conn.autocommit = False
        except Exception as e:
            print(f"Database connection failed: {e}")
            self.conn = None
    
    def create_tables(self):
        """Create necessary database tables if they don't exist."""
        if not self.conn:
            return
            
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS research_history (
                    id SERIAL PRIMARY KEY,
                    query TEXT NOT NULL,
                    company_name VARCHAR(255),
                    short_summary TEXT,
                    full_report TEXT,
                    follow_up_questions JSONB,
                    verification JSONB,
                    recommendation VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index on created_at for faster queries
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at 
                ON research_history(created_at DESC)
            """)
            
            # Create index on company name for filtering
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_company_name 
                ON research_history(company_name)
            """)
            
            self.conn.commit()
    
    def save_research(
        self,
        query: str,
        company_name: str,
        short_summary: str,
        full_report: str,
        follow_up_questions: List[str],
        verification: Dict,
        recommendation: str
    ) -> int:
        """
        Save a research result to the database.
        Returns the ID of the saved record.
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO research_history 
                (query, company_name, short_summary, full_report, 
                 follow_up_questions, verification, recommendation)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                query,
                company_name,
                short_summary,
                full_report,
                json.dumps(follow_up_questions),
                json.dumps(verification),
                recommendation
            ))
            
            result = cur.fetchone()
            self.conn.commit()
            return result[0]
    
    def get_recent_searches(self, limit: int = 10) -> List[Dict]:
        """Get the most recent search queries."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    id,
                    query,
                    company_name,
                    short_summary,
                    recommendation,
                    created_at
                FROM research_history
                ORDER BY created_at DESC
                LIMIT %s
            """, (limit,))
            
            return [dict(row) for row in cur.fetchall()]
    
    def get_research_by_id(self, research_id: int) -> Optional[Dict]:
        """Get a specific research result by ID."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    id,
                    query,
                    company_name,
                    short_summary,
                    full_report,
                    follow_up_questions,
                    verification,
                    recommendation,
                    created_at
                FROM research_history
                WHERE id = %s
            """, (research_id,))
            
            row = cur.fetchone()
            return dict(row) if row else None
    
    def search_by_company(self, company_name: str, limit: int = 10) -> List[Dict]:
        """Search for research results by company name."""
        with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    id,
                    query,
                    company_name,
                    short_summary,
                    recommendation,
                    created_at
                FROM research_history
                WHERE company_name ILIKE %s
                ORDER BY created_at DESC
                LIMIT %s
            """, (f'%{company_name}%', limit))
            
            return [dict(row) for row in cur.fetchall()]
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
