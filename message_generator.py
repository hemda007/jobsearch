"""Generates contextual LinkedIn cold messages via Claude API."""

import claude_client


def generate_messages(
    referrals: list[dict],
    resume_data: dict,
    jd_data: dict,
) -> list[str]:
    """
    Generate personalized LinkedIn connection request messages for all referrals
    in a single Claude API call.

    Args:
        referrals: list of dicts with name, title, url, connection_type
        resume_data: parsed resume dict
        jd_data: parsed JD dict

    Returns:
        List of message strings (one per referral, max ~280 chars each).
    """
    # Separate real profiles from fallback placeholders
    real_profiles = []
    messages = []
    index_map = {}  # maps position in real_profiles -> position in referrals

    for i, person in enumerate(referrals):
        if person.get("name") == "Could not find profile":
            messages.append("N/A — no profile found for this slot.")
        else:
            index_map[len(real_profiles)] = i
            real_profiles.append(person)
            messages.append(None)  # placeholder

    if not real_profiles:
        return messages

    top_skills = ", ".join(resume_data.get("skills", [])[:5])
    projects = resume_data.get("projects", [])
    most_relevant_project = projects[0] if projects else "data engineering pipeline project"
    top_requirements = ", ".join(jd_data.get("required_skills", [])[:3])
    job_title = jd_data.get("job_title", "Data Engineer")
    company_name = jd_data.get("company_name", "the company")

    # Build a single prompt for all real profiles
    people_blocks = []
    for idx, person in enumerate(real_profiles, 1):
        people_blocks.append(
            f"PERSON {idx}:\n"
            f"- Name: {person['name']}\n"
            f"- Title: {person['title']}\n"
            f"- Connection type: {person['connection_type']}"
        )

    prompt = f"""Write {len(real_profiles)} LinkedIn connection request message(s) (max 280 characters EACH) from a job seeker to potential referral contacts.

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

COMPANY & ROLE:
- Company: {company_name}
- Role: {job_title}
- Key requirements: {top_requirements}

{chr(10).join(people_blocks)}

Return ONLY valid JSON — an array of {len(real_profiles)} message string(s), in order:
["message for person 1", "message for person 2", ...]"""

    try:
        raw = claude_client.call_claude(prompt, max_tokens=512)
        parsed = claude_client.extract_json(raw)

        if isinstance(parsed, list):
            for idx, msg in enumerate(parsed):
                if idx < len(real_profiles):
                    msg = str(msg).strip()
                    if msg.startswith('"') and msg.endswith('"'):
                        msg = msg[1:-1]
                    if len(msg) > 280:
                        msg = msg[:277] + "..."
                    referral_idx = index_map[idx]
                    messages[referral_idx] = msg
    except Exception as e:
        print(f"  Batch message generation failed, falling back to individual: {e}")

    # Fill any remaining None slots (fallback for parse failures)
    for i, msg in enumerate(messages):
        if msg is None:
            messages[i] = "[Message generation failed]"

    return messages
