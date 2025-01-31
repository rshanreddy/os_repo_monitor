# weekly_osmonitor.py

import os
from datetime import datetime
import pandas as pd
import logging

from core_monitor import run_repo_tracking, anthropic_client, post_to_basecamp

def generate_weekly_analysis(df):
    """
    Summarize the top 5 AI repos by weekly % star growth.
    """
    prompt = f"""Summarize the top 5 AI repos by weekly % star growth:
{df.to_string()}

Focus on weekly changes only."""
    
    logging.info(f"Prompt to Claude for weekly analysis:\n{prompt}")
    try:
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        logging.error(f"Error generating weekly analysis: {e}")
        return "Error generating weekly analysis."

def generate_weekly_report(df, analysis_text=""):
    """
    Build a Markdown report focusing on top weekly growth.
    """
    if 'created_at' in df.columns:
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')

    timestamp = datetime.now().strftime('%Y-%m-%d')
    top_10_weekly = df.nlargest(10, 'weekly_pct')

    report = f"""# Weekly AI Repos Report
Generated on {timestamp}

## Weekly Analysis
{analysis_text}

## Top 10 Weekly Growth
"""

    for _, repo in top_10_weekly.iterrows():
        repo_created = (repo['created_at'].strftime('%Y-%m-%d') 
                        if pd.notnull(repo['created_at']) else "Unknown")
        report += f"""### {repo['repo_name']}
- ⭐ Stars: {repo['stars']:,} 
- 📈 1-Week Growth: {repo['weekly_diff']:,} stars ({repo['weekly_pct']:.2f}%)
- 🎂 Created: {repo_created}
- 🔍 Description: {repo['description']}
- 🔗 [Repo Link](https://github.com/{repo['repo_name']})

"""

    return report

if __name__ == "__main__":
    try:
        # 1) Update DB / get current snapshot
        df = run_repo_tracking()
        if df.empty:
            logging.error("No data collected, exiting.")
            exit(1)

        # 2) Weekly analysis
        analysis = generate_weekly_analysis(df.nlargest(5, 'weekly_pct'))

        # 3) Build the weekly Markdown report
        weekly_md = generate_weekly_report(df, analysis_text=analysis)
        
        # 4) Create a folder in logs/weekly/<timestamp>
        timestamp_full = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        folder_name = os.path.join("logs", "weekly", timestamp_full)
        os.makedirs(folder_name, exist_ok=True)
        
        # 5) Save the .md file
        md_path = os.path.join(folder_name, f"weekly_report_{timestamp_full}.md")
        with open(md_path, "w") as f:
            f.write(weekly_md)
        
        # 6) (Optional) also store a CSV
        csv_path = os.path.join(folder_name, f"weekly_repos_{timestamp_full}.csv")
        df.to_csv(csv_path, index=False)

        logging.info(f"Weekly report created: {md_path}")

        # 7) Post to Basecamp
        post_to_basecamp(md_path, subject="Weekly OS Report")
        logging.fino(f"Weekly report created: {md_path}")

    except Exception as e:
        logging.error(f"Error in weekly script: {e}")