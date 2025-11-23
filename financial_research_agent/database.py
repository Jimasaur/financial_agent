"""
Database module for storing financial research history.
Supports PostgreSQL (production) and SQLite (local development).
"""
import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Union, Any

# Try importing psycopg2, but don't fail if it's not installed (for local dev without Postgres)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False
    RealDictCursor = None


class ResearchDatabase:
    """Manages storage and retrieval of research history."""
    
    def __init__(self):
        """Initialize database connection."""
        self.conn = None
        self.db_type = 'sqlite'  # Default to sqlite
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Connect to the database (PostgreSQL or SQLite)."""
        try:
            database_url = os.getenv('DATABASE_URL')
            
            if database_url and HAS_POSTGRES:
                # Use DATABASE_URL (for Heroku, Railway, etc.)
                self.db_type = 'postgres'
                self.conn = psycopg2.connect(database_url)
                self.conn.autocommit = False
                print("Connected to PostgreSQL database")
            elif os.getenv('DB_HOST') and HAS_POSTGRES:
                 # Explicit Postgres config
                self.db_type = 'postgres'
                self.conn = psycopg2.connect(
                    host=os.getenv('DB_HOST'),
                    port=os.getenv('DB_PORT', '5432'),
                    database=os.getenv('DB_NAME', 'financial_research'),
                    user=os.getenv('DB_USER', 'postgres'),
                    password=os.getenv('DB_PASSWORD', 'postgres')
                )
                self.conn.autocommit = False
                print("Connected to PostgreSQL database (local config)")
            else:
                # Fallback to SQLite
                self.db_type = 'sqlite'
                db_path = 'financial_research.db'
                self.conn = sqlite3.connect(db_path, check_same_thread=False)
                
                # Enable row factory for dict-like access
                self.conn.row_factory = sqlite3.Row
                print(f"Connected to SQLite database ({db_path})")
                
        except Exception as e:
            print(f"Database connection failed: {e}")
            self.conn = None

    def _get_cursor(self):
        """Get a cursor with dict-like access."""
        if not self.conn:
            return None
            
        if self.db_type == 'postgres':
            return self.conn.cursor(cursor_factory=RealDictCursor)
        else:
            return self.conn.cursor()

    def create_tables(self):
        """Create necessary database tables if they don't exist."""
        if not self.conn:
            return
            
        cursor = self.conn.cursor()
        try:
            if self.db_type == 'postgres':
                cursor.execute("""
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
                
                # Create indexes
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_created_at 
                    ON research_history(created_at DESC)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_company_name 
                    ON research_history(company_name)
                """)
                
            else:  # SQLite
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS research_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query TEXT NOT NULL,
                        company_name TEXT,
                        short_summary TEXT,
                        full_report TEXT,
                        follow_up_questions TEXT,
                        verification TEXT,
                        recommendation TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_created_at 
                    ON research_history(created_at DESC)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_company_name 
                    ON research_history(company_name)
                """)
            
            self.conn.commit()
        except Exception as e:
            print(f"Error creating tables: {e}")
            self.conn.rollback()
        finally:
            cursor.close()
    
    def save_research(
        self,
        query: str,
        company_name: str,
        short_summary: str,
        full_report: str,
        follow_up_questions: List[str],
        verification: Dict,
        recommendation: str
    ) -> Optional[int]:
        """
        Save a research result to the database.
        Returns the ID of the saved record.
        """
        if not self.conn:
            return None
            
        cursor = self.conn.cursor()
        try:
            follow_up_json = json.dumps(follow_up_questions)
            verification_json = json.dumps(verification)
            
            if self.db_type == 'postgres':
                cursor.execute("""
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
                    follow_up_json,
                    verification_json,
                    recommendation
                ))
                result = cursor.fetchone()
                new_id = result['id'] if isinstance(result, dict) else result[0]
            else:  # SQLite
                cursor.execute("""
                    INSERT INTO research_history 
                    (query, company_name, short_summary, full_report, 
                     follow_up_questions, verification, recommendation)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    query,
                    company_name,
                    short_summary,
                    full_report,
                    follow_up_json,
                    verification_json,
                    recommendation
                ))
                new_id = cursor.lastrowid
                
            self.conn.commit()
            return new_id
        except Exception as e:
            print(f"Error saving research: {e}")
            self.conn.rollback()
            return None
        finally:
            cursor.close()
    
    def get_recent_searches(self, limit: int = 10) -> List[Dict]:
        """Get the most recent search queries."""
        if not self.conn:
            return []
            
        cursor = self._get_cursor()
        try:
            query_str = """
                SELECT 
                    id,
                    query,
                    company_name,
                    short_summary,
                    recommendation,
                    created_at
                FROM research_history
                ORDER BY created_at DESC
                LIMIT {}
            """.format('%s' if self.db_type == 'postgres' else '?')
            
            cursor.execute(query_str, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching history: {e}")
            return []
        finally:
            cursor.close()
    
    def get_research_by_id(self, research_id: int) -> Optional[Dict]:
        """Get a specific research result by ID."""
        if not self.conn:
            return None
            
        cursor = self._get_cursor()
        try:
            query_str = """
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
                WHERE id = {}
            """.format('%s' if self.db_type == 'postgres' else '?')
            
            cursor.execute(query_str, (research_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
                
            result = dict(row)
            
            # Parse JSON fields for SQLite (Postgres handles this automatically with JSONB but psycopg2 might return dict or str depending on configuration)
            # Actually, for SQLite, we stored them as TEXT, so we need to parse.
            # For Postgres with psycopg2 and JSONB, it usually returns Python objects.
            
            if self.db_type == 'sqlite':
                if isinstance(result.get('follow_up_questions'), str):
                    try:
                        result['follow_up_questions'] = json.loads(result['follow_up_questions'])
                    except:
                        result['follow_up_questions'] = []
                
                if isinstance(result.get('verification'), str):
                    try:
                        result['verification'] = json.loads(result['verification'])
                    except:
                        result['verification'] = {}
            
            return result
        except Exception as e:
            print(f"Error fetching research: {e}")
            return None
        finally:
            cursor.close()
    
    def search_by_company(self, company_name: str, limit: int = 10) -> List[Dict]:
        """Search for research results by company name."""
        if not self.conn:
            return []
            
        cursor = self._get_cursor()
        try:
            # Use ILIKE for Postgres, LIKE for SQLite (SQLite LIKE is case-insensitive for ASCII)
            op = 'ILIKE' if self.db_type == 'postgres' else 'LIKE'
            placeholder = '%s' if self.db_type == 'postgres' else '?'
            
            query_str = f"""
                SELECT 
                    id,
                    query,
                    company_name,
                    short_summary,
                    recommendation,
                    created_at
                FROM research_history
                WHERE company_name {op} {placeholder}
                ORDER BY created_at DESC
                LIMIT {placeholder}
            """
            
            cursor.execute(query_str, (f'%{company_name}%', limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error searching by company: {e}")
            return []
        finally:
            cursor.close()
    
    def clear_history(self):
        """Clear all research history."""
        if not self.conn:
            return
            
        cursor = self.conn.cursor()
        try:
            cursor.execute("DELETE FROM research_history")
            self.conn.commit()
        except Exception as e:
            print(f"Error clearing history: {e}")
            self.conn.rollback()
        finally:
            cursor.close()

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
