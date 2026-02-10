"""Extracts structured info from job description text using Claude API."""

import json
import time

import anthropic

import config


def parse_jd(jd_text: str) -> dict:
    """
    Parse job description text into structured data using Claude API.

    Returns dict with: job_title, company_name, location, required_skills,
    preferred_skills, experience_required, key_responsibilities, domain.
    """
    if not config.ANTHROPIC_API_KEY:
        raise ValueError(
            "ANTHROPIC_API_KEY not set. Create a .env file with your API key.\n"
            "See .env.example for the format."
        )

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

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

    try:
        response = client.messages.create(
            model=config.MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = response.content[0].text.strip()

        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        parsed = json.loads(response_text)

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

    except anthropic.APIError as e:
        # Retry once with backoff
        print(f"  Claude API error, retrying in 5s: {e}")
        time.sleep(5)
        response = client.messages.create(
            model=config.MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = response.content[0].text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        return json.loads(response_text)
