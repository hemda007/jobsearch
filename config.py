"""Configuration for Job Search Intelligence Tool."""

import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")  # Optional: free tier at serpapi.com (100 searches/month)
RESUME_PATH = os.path.join(os.path.dirname(__file__), "resume", "Peter_Pandey_Data_Engineer_Resume.pdf")
TRACKER_PATH = os.path.join(os.path.dirname(__file__), "tracker", "my_job_application_tracker.xlsx")
PARSED_RESUME_CACHE = os.path.join(os.path.dirname(__file__), "resume", ".parsed_resume.json")

MODEL = "claude-sonnet-4-5-20250929"
GOOGLE_SEARCH_PAUSE = 5  # seconds between Google searches
API_CALL_DELAY = 2  # seconds between Claude API calls
GOOGLE_RATE_LIMIT_WAIT = 30  # seconds to wait if rate limited
