# os_repo_monitor
This library includes tools for monitoring interesting open-source repositories on GitHub. The pre-loaded search queries generate reporting specifically for AI/LLM-focused repos with over 500 stars but the query terms are easy to interchange for other terms depending on your intended usage.

**daily_osmonitor and weekly_osmonitor**
track and analyze trending AI/ML repositories on GitHub, generating daily and weekly reports with growth metrics and intelligent summaries.

## Features
🤖 Tracks AI/ML repositories using GitHub's search API
📊 Calculates daily and weekly growth metrics
🧠 Uses Claude 3.5 to analyze trends and generate insights
📝 Generates structured Markdown reports
📈 Syncs data to Airtable for persistent tracking
📫 Posts reports to Basecamp automatically
🗄️ SQLite database for historical tracking

## Setup
1. Clone the repository
2. Install dependencies:
   pip install -r requirements.txt
3. Create a .env file with the following variables:
   
   GitHub App credentials
   APP_ID=
   PRIVATE_KEY_PATH=
   INSTALLATION_ID=

   Anthropic API
   ANTHROPIC_TOKEN=

   Airtable credentials
   AIRTABLE_API_KEY=
   AIRTABLE_BASE_ID=
   AIRTABLE_TABLE_NAME=

   Basecamp credentials
   BASECAMP_ACCOUNT_ID=
   BASECAMP_PROJECT_ID=
   BASECAMP_ACCESS_TOKEN=

# Usage: Daily Monitoring

Run: python daily_osmonitor.py. Generates a weekly summary with:
- Week-over-week growth analysis
- Top 10 repositories by weekly growth

# Project Structure
- core_monitor.py: Core functionality for GitHub API interaction and data processing
- daily_osmonitor.py: Daily monitoring and reporting script
- weekly_osmonitor.py: Weekly monitoring and reporting script
- repos.db: SQLite database for historical tracking
- logs/: Directory containing generated reports and CSVs

# Configuration
The search query can be modified in core_monitor.py:
  SEARCH_QUERY = "(gpt OR llm OR 'generative ai OR finetuning OR agent') in:name,description,readme stars:>500"
  MAX_REPOS = 800

# Output
Reports are generated in both Markdown and CSV formats, stored in:
logs/daily/<timestamp>/
logs/weekly/<timestamp>/
Data is also synced to Airtable and posted to Basecamp for team visibility.
