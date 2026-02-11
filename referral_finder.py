"""Finds real LinkedIn profiles via SerpAPI (preferred) or Google search fallback."""

import json
import re
import time
import urllib.parse
import urllib.request

import config


def _parse_linkedin_title(title: str, description: str = "") -> tuple[str, str]:
    """Extract name and title from a LinkedIn search result."""
    name = ""
    person_title = ""

    if title:
        title_clean = title.replace(" | LinkedIn", "").replace(" - LinkedIn", "")
        parts = title_clean.split(" - ", 1)
        if len(parts) >= 2:
            name = parts[0].strip()
            person_title = parts[1].strip()
        elif len(parts) == 1:
            name = parts[0].strip()

    if not name and description:
        name_match = re.match(r"^([A-Z][a-z]+ [A-Z][a-z]+)", description)
        if name_match:
            name = name_match.group(1)

    if not person_title and description:
        person_title = description[:100]

    return name or "Unknown", person_title or "Professional"


def _search_serpapi(query: str, num_results: int = 5) -> list[dict]:
    """Search using SerpAPI (reliable, free tier: 100 searches/month)."""
    profiles = []
    params = urllib.parse.urlencode({
        "q": query,
        "api_key": config.SERPAPI_API_KEY,
        "engine": "google",
        "num": num_results,
    })
    url = f"https://serpapi.com/search.json?{params}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        for result in data.get("organic_results", []):
            link = result.get("link", "")
            if "linkedin.com/in/" not in link:
                continue

            link = link.split("?")[0]
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            name, person_title = _parse_linkedin_title(title, snippet)

            profiles.append({
                "name": name,
                "title": person_title,
                "url": link,
            })
    except Exception as e:
        print(f"  SerpAPI error: {e}")

    return profiles


def _search_google_fallback(query: str, num_results: int = 5) -> list[dict]:
    """Fallback: use googlesearch-python package."""
    profiles = []
    try:
        from googlesearch import search
        results = search(query, num_results=num_results, advanced=True)
        for result in results:
            url = result.url if hasattr(result, "url") else str(result)
            title = result.title if hasattr(result, "title") else ""
            description = result.description if hasattr(result, "description") else ""

            if "linkedin.com/in/" not in url:
                continue

            url = url.split("?")[0]
            name, person_title = _parse_linkedin_title(title, description)

            profiles.append({
                "name": name,
                "title": person_title,
                "url": url,
            })
    except Exception as e:
        print(f"  Google search error for '{query[:50]}...': {e}")

    return profiles


def _search(query: str, num_results: int = 5) -> list[dict]:
    """Search using best available method."""
    if config.SERPAPI_API_KEY:
        return _search_serpapi(query, num_results)
    return _search_google_fallback(query, num_results)


def find_referrals(company_name: str, job_title: str) -> list[dict]:
    """
    Find 3 real LinkedIn profiles at the target company.

    Uses SerpAPI if SERPAPI_API_KEY is set (reliable), otherwise falls back
    to googlesearch-python (can get blocked by Google).

    Returns list of up to 3 dicts with: name, title, url, connection_type.
    """
    if config.SERPAPI_API_KEY:
        print("  Using SerpAPI for profile search")
    else:
        print("  Using Google search (tip: add SERPAPI_API_KEY to .env for better results)")

    referrals = []
    seen_urls = set()

    searches = [
        {
            "query": f'site:linkedin.com/in "{company_name}" "{job_title}"',
            "connection_type": "same_role",
        },
        {
            "query": f'site:linkedin.com/in "{company_name}" "Engineering Manager" OR "Data Lead" OR "Head of Data"',
            "connection_type": "hiring_manager",
        },
        {
            "query": f'site:linkedin.com/in "{company_name}" "Data Engineer" OR "Analytics Engineer" OR "Software Engineer"',
            "connection_type": "peer",
        },
    ]

    for i, search_config in enumerate(searches):
        if len(referrals) >= 3:
            break

        if i > 0:
            time.sleep(config.GOOGLE_SEARCH_PAUSE)

        try:
            profiles = _search(search_config["query"])
        except Exception:
            print(f"  Rate limited on search {i + 1}, waiting {config.GOOGLE_RATE_LIMIT_WAIT}s...")
            time.sleep(config.GOOGLE_RATE_LIMIT_WAIT)
            try:
                profiles = _search(search_config["query"])
            except Exception as e:
                print(f"  Search still failing: {e}")
                profiles = []

        for profile in profiles:
            if profile["url"] not in seen_urls:
                profile["connection_type"] = search_config["connection_type"]
                referrals.append(profile)
                seen_urls.add(profile["url"])
                break

    # Broader fallback if we don't have 3
    if len(referrals) < 3:
        time.sleep(config.GOOGLE_SEARCH_PAUSE)
        try:
            profiles = _search(f'site:linkedin.com/in "{company_name}" engineer', num_results=10)
            for profile in profiles:
                if len(referrals) >= 3:
                    break
                if profile["url"] not in seen_urls:
                    profile["connection_type"] = "peer"
                    referrals.append(profile)
                    seen_urls.add(profile["url"])
        except Exception as e:
            print(f"  Fallback search failed: {e}")

    # Fill remaining slots with manual search links
    while len(referrals) < 3:
        search_url = "https://www.google.com/search?" + urllib.parse.urlencode({
            "q": f'site:linkedin.com/in "{company_name}" "{job_title}"'
        })
        referrals.append({
            "name": "Could not find profile",
            "title": "Try searching manually",
            "url": search_url,
            "connection_type": "unknown",
        })

    return referrals[:3]
