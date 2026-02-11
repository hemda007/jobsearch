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
            messages.append("N/A - no profile found for this slot.")
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

    prompt = f"""You are ghostwriting LinkedIn connection requests for a real person. These must read like a human typed them on their phone. Zero AI smell.

Write {len(real_profiles)} connection request message(s). Max 280 characters EACH.

ABSOLUTE RULES:
- Sound like a real human, not a bot. Think "quick message at a coffee shop" energy.
- NEVER use em dashes. Use periods, commas, or just start a new thought.
- NEVER use semicolons.
- NEVER say: "leverage", "synergy", "passionate", "keen", "eager", "excited", "thrilled", "delighted", "invaluable", "insightful"
- NEVER start with: "Hi [Name]", "Hey!", "I came across", "I noticed", "I'd love to connect", "I'm reaching out", "Hope this finds you"
- NEVER ask for a job or referral. Ever.
- Use lowercase naturally. Don't overcapitalize.
- Use contractions (i'm, you're, what's)
- One or two sentences max. Short. Punchy.
- Lead with a specific shared interest (a tool, a tech, a problem you both deal with)
- End with a low-pressure question

TONE BY WHO THEY ARE:
- same_role: talk shop, mention a specific tool you both use. "been working with [X] on a pipeline project. saw you're doing similar stuff at {company_name}, curious how [Y] is working out for you?"
- hiring_manager: show you get what their team does. don't ask for anything. "your data team's growth at {company_name} caught my eye. i built something similar with [tech]. would be cool to hear how you all approach [problem]"
- peer: keep it super casual. "fellow data person here. been deep in [tech] lately, curious what the stack looks like at {company_name}"

GOOD (copy this energy):
- "been building spark pipelines on AWS lately. saw your team at {company_name} uses kafka too. curious how you handle schema changes at that scale?"
- "just finished migrating a warehouse to snowflake. {company_name}'s data team seems to be growing fast. what does the tooling look like on the inside?"
- "fellow data engineer here, been working with airflow and dbt. curious what orchestration looks like at {company_name}?"

BAD (never do this):
- "Hi Rahul, I'm a data engineer passionate about building scalable pipelines. I'd love to connect and learn about your experience at IBM."
- "Hello! I noticed your impressive profile. I'm eager to explore opportunities and would appreciate any insights you might share."
- "I'm reaching out because I'm very interested in the Data Engineer role at your esteemed company. I believe my skills in Python and SQL make me a strong candidate."

ABOUT THE SENDER:
- Name: Peter Pandey
- Skills: {top_skills}
- Recent project: {most_relevant_project}
- Looking at: {job_title} at {company_name}
- Role needs: {top_requirements}

{chr(10).join(people_blocks)}

Return ONLY a JSON array of {len(real_profiles)} message string(s):
["msg1", "msg2", ...]"""

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
