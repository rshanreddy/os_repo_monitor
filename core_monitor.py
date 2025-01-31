# core_monitor.py
import os
import sqlite3
from datetime import datetime, timedelta
from pyairtable import Table
import pandas as pd
import logging
import json
import markdown
import requests

from github import Github, GithubIntegration
import anthropic

from dotenv import load_dotenv
import os

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = "All Repos"

BASECAMP_ACCOUNT_ID = os.getenv("BASECAMP_ACCOUNT_ID")
BASECAMP_PROJECT_ID = os.getenv("BASECAMP_PROJECT_ID")
BASECAMP_ACCESS_TOKEN = os.getenv("BASECAMP_ACCESS_TOKEN")

# ======== YOUR CONFIG ========
APP_ID = os.getenv("APP_ID")
PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH")
INSTALLATION_ID = os.getenv("INSTALLATION_ID")
DB_PATH = "repos.db"
SEARCH_QUERY = "(gpt OR llm OR 'generative ai OR finetuning OR agent') in:name,description,readme stars:>500"
MAX_REPOS = 800

with open(PRIVATE_KEY_PATH, 'r') as key_file:
    private_key = key_file.read()

git_integration = GithubIntegration(APP_ID, private_key)

def get_github_client():
    token = git_integration.get_access_token(INSTALLATION_ID)
    return Github(token.token)

github_client = get_github_client()

ANTHROPIC_API_KEY = ANTHROPIC_TOKEN = os.getenv("ANTHROPIC_TOKEN")
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_TOKEN)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('repo_tracker.log'),
        logging.StreamHandler()
    ]
)

def init_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS repo_stats (
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
    conn.commit()
    conn.close()

def summarize_readme_if_needed(repo):
    if repo.description and repo.description.strip():
        logging.info(f"Using existing description for {repo.full_name}")
        return repo.description
    try:
        readme_content = repo.get_readme().decoded_content.decode("utf-8")
        cleaned_text = ' '.join(readme_content.split())[:1000]
        prompt = f"Technical one-line description of this project:\n{cleaned_text}"
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        logging.error(f"Error summarizing README: {e}")
        return None

def store_repo_data(repo_full_name, stars, forks, created_at, updated_at, description):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO repo_stats (repo_full_name, star_count, forks_count, timestamp, created_at, updated_at, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        repo_full_name,
        stars,
        forks,
        datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
        created_at.strftime('%Y-%m-%d %H:%M:%S'),
        updated_at.strftime('%Y-%m-%d %H:%M:%S'),
        description,
    ))
    conn.commit()
    conn.close()

def get_historical_star_count(repo_full_name, days_ago=7):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    target_time = datetime.utcnow() - timedelta(days=days_ago)
    c.execute("""
        SELECT star_count
        FROM repo_stats
        WHERE repo_full_name = ?
          AND timestamp <= ?
        ORDER BY timestamp DESC
        LIMIT 1
    """, (
        repo_full_name,
        target_time.strftime('%Y-%m-%d %H:%M:%S')
    ))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def compute_star_diff(repo_full_name, current_stars):
    # daily
    old_stars_1d = get_historical_star_count(repo_full_name, days_ago=1)
    daily_diff = (current_stars - old_stars_1d) if old_stars_1d else 0
    daily_pct = (daily_diff / old_stars_1d * 100) if (old_stars_1d and old_stars_1d>0) else 0.0

    # weekly
    old_stars_7d = get_historical_star_count(repo_full_name, days_ago=7)
    weekly_diff = (current_stars - old_stars_7d) if old_stars_7d else 0
    weekly_pct = (weekly_diff / old_stars_7d * 100) if (old_stars_7d and old_stars_7d>0) else 0.0

    return daily_diff, daily_pct, weekly_diff, weekly_pct

def get_last_db_update_time():
    """
    Returns the most recent timestamp (max) from repo_stats.
    If table is empty, returns None.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT MAX(timestamp) FROM repo_stats")
    row = c.fetchone()
    conn.close()
    if row and row[0]:
        return row[0]  # This is a string like "2025-01-30 10:44:02" by default
    return None

def get_db_row_count():
    """
    Returns how many total rows are in repo_stats.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM repo_stats")
    row = c.fetchone()
    conn.close()
    return row[0] if row else 0

def run_repo_tracking():
    logging.info("Initializing DB...")
    init_database()
    logging.info(f"Searching GitHub with query:\n{SEARCH_QUERY}")
    results = github_client.search_repositories(query=SEARCH_QUERY, sort='stars', order='desc')

    data_rows = []
    count = 0
    for repo in results:
        if MAX_REPOS and count >= MAX_REPOS:
            break
        
        repo_full_name = repo.full_name
        stars = repo.stargazers_count
        forks = repo.forks_count
        created_at = repo.created_at
        updated_at = repo.updated_at
        
        description = summarize_readme_if_needed(repo)
        store_repo_data(repo_full_name, stars, forks, created_at, updated_at, description)
        
        daily_diff, daily_pct, weekly_diff, weekly_pct = compute_star_diff(repo_full_name, stars)
        row = {
            "repo_name": repo_full_name,
            "stars": stars,
            "daily_diff": daily_diff,
            "daily_pct": daily_pct,
            "weekly_diff": weekly_diff,
            "weekly_pct": weekly_pct,
            "created_at": created_at,
            "updated_at": updated_at,
            "description": description
        }
        data_rows.append(row)
        count += 1
    logging.info(f"Processed {count} repos.")
    
    df = pd.DataFrame(data_rows)
    df.to_csv("latest_repos.csv", index=False)
    logging.info("Saved current snapshot to latest_repos.csv")
    return df

def sync_df_to_airtable(df):
    """
    Overwrites (or upserts) all rows in Airtable from the given DataFrame.
    Each row is keyed by 'repo_name' (so it won't create duplicates if you run multiple times).
    Alternatively, you can 'batch_create' if you want to always add new rows.
    """

    # Initialize the table
    table = Table(AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

    # Convert your DataFrame to a list of dictionaries
    records_list = df.to_dict(orient="records")

    # OPTIONAL: If you want to start fresh each time, you can delete existing records
    # (Beware if you want to keep old data or have multiple runs a day)
    # existing_records = table.all()
    # existing_ids = [record['id'] for record in existing_records]
    # for chunk in [existing_ids[i:i+10] for i in range(0, len(existing_ids), 10)]:
    #     table.batch_delete(chunk)

    # Use 'batch_upsert' to update if 'repo_name' is the same, otherwise insert new
    # This requires you specify which field is your "unique key" in Airtable
    # Make sure your table in Airtable has a "Repo Name" (or something) that lines up with 'repo_name' below
    # If your primary field in Airtable is the 'Name' column, rename accordingly
    def record_mapper(record):
        # Map your DataFrame fields to Airtable fields
        # e.g. "Name" might be the primary field in Airtable
        return {
            "Name": record["repo_name"],
            "Stars": record["stars"],
            "Daily Diff": record["daily_diff"],
            "Daily %": record["daily_pct"],
            "Weekly Diff": record["weekly_diff"],
            "Weekly %": record["weekly_pct"],
            "Created At": str(record["created_at"]),
            "Updated At": str(record["updated_at"]),
            "Description": record["description"],
        }

    mapped_records = [{"fields": record_mapper(r)} for r in records_list]

    # Upsert them in batches. 
    # 'field_name' must match the primary field in your Airtable if you want to match existing rows.
    # If your "Name" field in Airtable is the primary, pass "Name"
    result = table.batch_upsert(
        records=mapped_records, 
        key_fields=["Name"], 
        typecast=True
    )
    logging.info(f"Upserted {len(result)} records into Airtable.")

def post_to_basecamp(md_file_path, subject="Daily OS Report"):
    """
    Converts the .md file at md_file_path to HTML, then creates a new message
    in the specified Basecamp project.
    """
    # 1) Convert MD to HTML
    with open(md_file_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    html_body = markdown.markdown(md_text)

    # 2) Build request
    headers = {
        "Authorization": f"Bearer {BASECAMP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "DailyOSMonitor (someone@example.com)"  # BC requires a UA
    }

    message_endpoint = f"https://3.basecampapi.com/{3785609}/buckets/{40885683}/message_boards/8279891628/messages.json"

    post_data = {
        "subject": subject,
        "content": html_body,
        "status": "active"
    }

    # 3) Send request
    r = requests.post(message_endpoint, headers=headers, data=json.dumps(post_data))
    if r.status_code == 201:
        logging.info(f"Posted '{subject}' to Basecamp successfully!")
    else:
        logging.error(f"Error posting to Basecamp: {r.status_code} => {r.text}")
