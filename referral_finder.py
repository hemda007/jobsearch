"""Finds real LinkedIn profiles via Google search."""

import re
import time
import urllib.parse

from googlesearch import search

import config


def _search_linkedin(query: str, num_results: int = 5) -> list[dict]:
    """
    Search Google for LinkedIn profiles matching the query.
    Returns list of dicts with url, name, title extracted from results.
    """
    profiles = []
    try:
        results = search(query, num_results=num_results, advanced=True)
        for result in results:
            url = result.url if hasattr(result, "url") else str(result)
            title = result.title if hasattr(result, "title") else ""
            description = result.description if hasattr(result, "description") else ""

            # Only keep linkedin.com/in/ profile URLs
            if "linkedin.com/in/" not in url:
                continue

            # Clean URL
            url = url.split("?")[0]  # Remove query params

            # Extract name from title (LinkedIn titles are usually "Name - Title | LinkedIn")
            name = ""
            person_title = ""
            if title:
                # Common LinkedIn title format: "First Last - Title | LinkedIn"
                title_clean = title.replace(" | LinkedIn", "").replace(" - LinkedIn", "")
                parts = title_clean.split(" - ", 1)
                if len(parts) >= 2:
                    name = parts[0].strip()
                    person_title = parts[1].strip()
                elif len(parts) == 1:
                    name = parts[0].strip()

            # Fallback: try to extract from description
            if not name and description:
                # Description often starts with the person's headline
                name_match = re.match(r"^([A-Z][a-z]+ [A-Z][a-z]+)", description)
                if name_match:
                    name = name_match.group(1)

            if not person_title and description:
                person_title = description[:100]  # Use first 100 chars of description

            profiles.append({
                "name": name or "Unknown",
                "title": person_title or "Professional",
                "url": url,
            })

    except Exception as e:
        print(f"  Google search error for '{query[:50]}...': {e}")

    return profiles


def find_referrals(company_name: str, job_title: str) -> list[dict]:
    """
    Find 3 real LinkedIn profiles at the target company.

    Runs 3 searches:
    1. People in the same role
    2. Potential hiring managers
    3. Peer-level engineers

    Returns list of up to 3 dicts with: name, title, url, connection_type.
    """
    referrals = []
    seen_urls = set()

    searches = [
        {
            "query": f'site:linkedin.com/in "{company_name}" "{job_title}"',
            "connection_type": "same_role",
            "label": "same role",
        },
        {
            "query": f'site:linkedin.com/in "{company_name}" "Engineering Manager" OR "Data Lead" OR "Head of Data"',
            "connection_type": "hiring_manager",
            "label": "hiring manager",
        },
        {
            "query": f'site:linkedin.com/in "{company_name}" "Data Engineer" OR "Analytics Engineer" OR "Software Engineer"',
            "connection_type": "peer",
            "label": "peer",
        },
    ]

    for i, search_config in enumerate(searches):
        if len(referrals) >= 3:
            break

        if i > 0:
            time.sleep(config.GOOGLE_SEARCH_PAUSE)

        try:
            profiles = _search_linkedin(search_config["query"])
        except Exception:
            # Rate limited — wait and retry once
            print(f"  Rate limited on search {i + 1}, waiting {config.GOOGLE_RATE_LIMIT_WAIT}s...")
            time.sleep(config.GOOGLE_RATE_LIMIT_WAIT)
            try:
                profiles = _search_linkedin(search_config["query"])
            except Exception as e:
                print(f"  Search still failing: {e}")
                profiles = []

        for profile in profiles:
            if profile["url"] not in seen_urls:
                profile["connection_type"] = search_config["connection_type"]
                referrals.append(profile)
                seen_urls.add(profile["url"])
                break  # Take only the first valid profile from each search

    # If we didn't get 3, try a broader fallback search
    if len(referrals) < 3:
        time.sleep(config.GOOGLE_SEARCH_PAUSE)
        try:
            fallback_query = f'site:linkedin.com/in "{company_name}" engineer'
            profiles = _search_linkedin(fallback_query, num_results=10)
            for profile in profiles:
                if len(referrals) >= 3:
                    break
                if profile["url"] not in seen_urls:
                    profile["connection_type"] = "peer"
                    referrals.append(profile)
                    seen_urls.add(profile["url"])
        except Exception as e:
            print(f"  Fallback search failed: {e}")

    # If we still have fewer than 3, fill with manual search suggestion
    while len(referrals) < 3:
        search_url = "https://www.google.com/search?" + urllib.parse.urlencode({
            "q": f'site:linkedin.com/in "{company_name}" "{job_title}"'
        })
        referrals.append({
            "name": "Could not find profile",
            "title": f"Try searching manually",
            "url": search_url,
            "connection_type": "unknown",
        })

    return referrals[:3]
