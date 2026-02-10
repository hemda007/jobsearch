"""Generates contextual LinkedIn cold messages via Claude API."""

import time

import anthropic

import config


def generate_message(
    person: dict,
    resume_data: dict,
    jd_data: dict,
) -> str:
    """
    Generate a personalized LinkedIn connection request message.

    Args:
        person: dict with name, title, url, connection_type
        resume_data: parsed resume dict
        jd_data: parsed JD dict

    Returns:
        Message string (max ~280 characters).
    """
    if not config.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set.")

    # Skip generating message for manual search fallbacks
    if person.get("name") == "Could not find profile":
        return "N/A — no profile found for this slot."

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)

    top_skills = ", ".join(resume_data.get("skills", [])[:5])
    projects = resume_data.get("projects", [])
    most_relevant_project = projects[0] if projects else "data engineering pipeline project"

    top_requirements = ", ".join(jd_data.get("required_skills", [])[:3])
    job_title = jd_data.get("job_title", "Data Engineer")
    company_name = jd_data.get("company_name", "the company")

    prompt = f"""Write a LinkedIn connection request message (max 280 characters) from a job seeker to a potential referral contact.

RULES:
- Be specific and contextual — reference something concrete from the candidate's background that connects to the person's role/company
- Do NOT be generic ("I'd love to connect" or "I'm reaching out because...")
- Do NOT be needy or desperate
- Be concise — this is a connection request, not a cover letter
- Sound human, warm, and specific
- End with a soft ask (learn about their experience, not "please refer me")

CANDIDATE PROFILE:
- Name: Peter Pandey
- Target role: {job_title} at {company_name}
- Key skills: {top_skills}
- Relevant project: {most_relevant_project}

REFERRAL PERSON:
- Name: {person['name']}
- Title: {person['title']}
- Company: {company_name}
- Connection type: {person['connection_type']} (peer / hiring_manager / same_role)

JOB CONTEXT:
- Role: {job_title}
- Key requirements: {top_requirements}

Return ONLY the message text, nothing else."""

    try:
        response = client.messages.create(
            model=config.MODEL,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        message = response.content[0].text.strip()

        # Remove surrounding quotes if present
        if message.startswith('"') and message.endswith('"'):
            message = message[1:-1]

        # Truncate to 280 chars if needed
        if len(message) > 280:
            message = message[:277] + "..."

        return message

    except anthropic.APIError as e:
        print(f"  Claude API error generating message, retrying in 5s: {e}")
        time.sleep(5)
        try:
            response = client.messages.create(
                model=config.MODEL,
                max_tokens=256,
                messages=[{"role": "user", "content": prompt}],
            )
            message = response.content[0].text.strip()
            if message.startswith('"') and message.endswith('"'):
                message = message[1:-1]
            if len(message) > 280:
                message = message[:277] + "..."
            return message
        except Exception as e2:
            return f"[Message generation failed: {e2}]"
