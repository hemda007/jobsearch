"""Uses Claude API to score resume-JD match % and find improvement areas."""

import json
import time

import anthropic

import config


def match_resume_to_jd(resume_data: dict, jd_data: dict, jd_text: str) -> dict:
    """
    Compare resume against job description and return match % and improvements.

    Returns dict with: match_percentage (int), improvements (list of 3 strings).
    """
    if not config.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set.")

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    resume_text = resume_data.get("raw_text", "")

    prompt = f"""You are a job matching expert. Compare this resume against the job description and provide:

1. A match percentage (0-100) based on:
   - Skills overlap (40% weight)
   - Experience level fit (25% weight)
   - Project relevance (20% weight)
   - Education & certifications (15% weight)

2. Exactly 3 specific, actionable areas where the candidate should improve to be a stronger fit for THIS specific role. Be concrete — mention specific skills, tools, or experiences to add.

Return ONLY valid JSON:
{{
  "match_percentage": 74,
  "improvements": [
    "1. Add Docker containerization to your pipeline projects — this role explicitly requires Docker and your resume has no container experience",
    "2. Learn dbt fundamentals and add a dbt project to your portfolio — the role requires dbt for data transformations and you currently have no dbt experience",
    "3. Deepen your AWS skills beyond S3/Glue to include Redshift and Lambda — the role requires full AWS data stack proficiency"
  ]
}}

RESUME:
{resume_text}

JOB DESCRIPTION:
{jd_text}"""

    try:
        response = client.messages.create(
            model=config.MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = response.content[0].text.strip()

        # Extract JSON from response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        result = json.loads(response_text)

        # Validate
        if "match_percentage" not in result:
            result["match_percentage"] = 50
        if "improvements" not in result or len(result["improvements"]) < 3:
            result["improvements"] = result.get("improvements", [])
            while len(result["improvements"]) < 3:
                result["improvements"].append("Review the full job description for additional requirements")

        result["match_percentage"] = max(0, min(100, int(result["match_percentage"])))

        return result

    except anthropic.APIError as e:
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
