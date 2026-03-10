"""
Database module for Image Detection Result Analyzer
Handles SQLite database schema and operations
"""
import sqlite3
import os
from contextlib import contextmanager


DATABASE_PATH = os.path.join('app', 'data', 'dataset_analysis.db')


@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize database with all required tables"""
    with get_db() as conn:
        cursor = conn.cursor()

        # Create dataset_metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dataset_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                total_images INTEGER DEFAULT 0,
                total_classes INTEGER DEFAULT 0,
                iou_threshold REAL DEFAULT 0.5,
                confidence_threshold REAL DEFAULT 0.5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create image_metadata table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS image_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                width INTEGER,
                height INTEGER,
                thumbnail_path TEXT,
                image_path TEXT,
                total_gt_boxes INTEGER DEFAULT 0,
                total_pred_boxes INTEGER DEFAULT 0,
                has_fp BOOLEAN DEFAULT 0,
                has_fn BOOLEAN DEFAULT 0,
                is_perfect BOOLEAN DEFAULT 0,
                FOREIGN KEY (dataset_id) REFERENCES dataset_metadata(id) ON DELETE CASCADE
            )
        ''')

        # Create classes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                total_gt_count INTEGER DEFAULT 0,
                total_pred_count INTEGER DEFAULT 0,
                tp_count INTEGER DEFAULT 0,
                fp_count INTEGER DEFAULT 0,
                fn_count INTEGER DEFAULT 0,
                recall REAL DEFAULT 0.0,
                precision REAL DEFAULT 0.0,
                fpr REAL DEFAULT 0.0,
                f1_score REAL DEFAULT 0.0,
                FOREIGN KEY (dataset_id) REFERENCES dataset_metadata(id) ON DELETE CASCADE,
                UNIQUE(dataset_id, name)
            )
        ''')

        # Create bounding_boxes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bounding_boxes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                class_id INTEGER NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('ground_truth', 'prediction')),
                x1 REAL NOT NULL,
                y1 REAL NOT NULL,
                x2 REAL NOT NULL,
                y2 REAL NOT NULL,
                confidence REAL,
                iou REAL,
                classification TEXT CHECK(classification IN ('tp', 'fp', 'fn') OR classification IS NULL),
                FOREIGN KEY (image_id) REFERENCES image_metadata(id) ON DELETE CASCADE,
                FOREIGN KEY (class_id) REFERENCES classes(id) ON DELETE CASCADE
            )
        ''')

        # Create indexes for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_image_filename ON image_metadata(filename)
        ''')

        # Migration: Add image_path column if it doesn't exist
        cursor.execute("PRAGMA table_info(image_metadata)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'image_path' not in columns:
            cursor.execute('ALTER TABLE image_metadata ADD COLUMN image_path TEXT')
            print("Migrated: Added image_path column to image_metadata table")
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_class_name ON classes(name)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_bbox_image_id ON bounding_boxes(image_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_bbox_class_id ON bounding_boxes(class_id)
        ''')

        conn.commit()

    print(f"Database initialized successfully at: {DATABASE_PATH}")


def get_table_schema(table_name):
    """Get the schema of a specific table for verification"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return cursor.fetchall()


def list_tables():
    """List all tables in the database"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [row[0] for row in cursor.fetchall()]


if __name__ == "__main__":
    # Test database initialization
    print("Initializing database...")
    init_db()

    print("\nTables created:")
    tables = list_tables()
    for table in tables:
        print(f"  - {table}")

    print("\nTable schemas:")
    for table in tables:
        print(f"\n{table}:")
        columns = get_table_schema(table)
        for col in columns:
            print(f"  {col[1]}: {col[2]}{' (PK)' if col[5] > 0 else ''}")
