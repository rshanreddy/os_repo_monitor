from analyzerepos import get_weekly_trending_repos  # assuming your original file is analyzerepos.py

import os
import sqlite3
import pandas as pd
from datetime import datetime

def test_weekly_calculations():
    """Simulates a week of data to verify our trending calculations"""
    
    # Create test database
    test_db = "test_repos.db"
    
    # Remove existing test db if it exists
    if os.path.exists(test_db):
        os.remove(test_db)
    
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    # Create schema
    cursor.execute("""
        CREATE TABLE repo_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_full_name TEXT,
            star_count INTEGER,
            forks_count INTEGER,
            timestamp DATETIME,
            created_at DATETIME,
            updated_at DATETIME,
            description TEXT
        )
    """)
    
    # Insert simulated data for 3 repos over 8 days
    test_data = [
        # Fast growing repo
        ("hot-repo/viral", 1000, "2025-01-20"),  # Day 1
        ("hot-repo/viral", 1200, "2025-01-26"),  # Day 7
        ("hot-repo/viral", 1300, "2025-01-27"),  # Today
        
        # Steady growth repo
        ("steady/growth", 5000, "2025-01-20"),
        ("steady/growth", 5250, "2025-01-26"),
        ("steady/growth", 5300, "2025-01-27"),
        
        # Slow growth repo
        ("slow/repo", 10000, "2025-01-20"),
        ("slow/repo", 10100, "2025-01-26"),
        ("slow/repo", 10110, "2025-01-27"),
    ]
    
    for repo, stars, date in test_data:
        cursor.execute(
            """
            INSERT INTO repo_stats 
            (repo_full_name, star_count, forks_count, timestamp, created_at, updated_at, description)
            VALUES (?, ?, 0, ?, ?, ?, ?)
            """,
            (repo, stars, date, date, date, f"Test repo {repo}")
        )
    
    conn.commit()
    
    # Test query
    query = """
    WITH latest_timestamp AS (
        SELECT MAX(timestamp) as max_ts FROM repo_stats
    ),
    current_stats AS (
        SELECT * FROM repo_stats r
        WHERE timestamp = (SELECT max_ts FROM latest_timestamp)
    )
    SELECT 
        c.repo_full_name,
        c.star_count as current_stars,
        c.description,
        COALESCE(c.star_count - d.star_count, 0) as daily_gain,
        CASE 
            WHEN d.star_count > 0 THEN ROUND(((c.star_count - d.star_count) * 100.0 / d.star_count), 2)
            ELSE 0 
        END as daily_pct,
        COALESCE(c.star_count - w.star_count, 0) as weekly_gain,
        CASE 
            WHEN w.star_count > 0 THEN ROUND(((c.star_count - w.star_count) * 100.0 / w.star_count), 2)
            ELSE 0 
        END as weekly_pct
    FROM current_stats c
    LEFT JOIN repo_stats d ON c.repo_full_name = d.repo_full_name 
        AND d.timestamp >= datetime((SELECT max_ts FROM latest_timestamp), '-1 day')
        AND d.timestamp < (SELECT max_ts FROM latest_timestamp)
    LEFT JOIN repo_stats w ON c.repo_full_name = w.repo_full_name
        AND w.timestamp >= datetime((SELECT max_ts FROM latest_timestamp), '-7 day')
        AND w.timestamp < (SELECT max_ts FROM latest_timestamp)
    ORDER BY weekly_pct DESC
    """
    
    df = pd.read_sql_query(query, conn)
    print("\nTest Results (should show hot-repo/viral first):")
    print(df[['repo_full_name', 'current_stars', 'daily_gain', 'daily_pct', 'weekly_gain', 'weekly_pct']])
    
    conn.close()
    os.remove(test_db)  # Cleanup

if __name__ == "__main__":
    test_weekly_calculations()