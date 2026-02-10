"""Extracts structured info from job description text using Claude API."""

import claude_client


def parse_jd(jd_text: str) -> dict:
    """
    Parse job description text into structured data using Claude API.

    Returns dict with: job_title, company_name, location, required_skills,
    preferred_skills, experience_required, key_responsibilities, domain.
    """
    prompt = f"""Extract structured information from this job description. Return ONLY valid JSON with these fields:
- job_title (string)
- company_name (string)
- location (string)
- required_skills (array of strings)
- preferred_skills (array of strings)
- experience_required (string)
- key_responsibilities (array of strings, max 5)
- domain (string, e.g. "Fintech", "HealthTech", "E-commerce")

Job Description:
{jd_text}"""

    parsed = claude_client.call_claude_json(prompt)

    # Ensure all expected fields exist
    defaults = {
        "job_title": "Unknown",
        "company_name": "Unknown",
        "location": "Unknown",
        "required_skills": [],
        "preferred_skills": [],
        "experience_required": "Not specified",
        "key_responsibilities": [],
        "domain": "Unknown",
    }
    for key, default in defaults.items():
        if key not in parsed:
            parsed[key] = default

    return parsed
