# YouTube Tutorial Plan: "Build a Job Search AI Tool with Claude Code"

## Context
Single long-form YouTube tutorial (~35-40 min) where a beginner audience learns two things at once:
1. **How to build a real Python project** — a Job Search Intelligence Tool
2. **How to use Claude Code** (Anthropic's AI coding CLI) to build it from scratch

**Roles**: Dhaval = moderator/host who guides the narrative, asks "dumb questions" beginners have. You = the executor who codes live with Claude Code.

---

## Video Title Options
- "I Built a Job Search AI Tool Using Only Claude Code"
- "Claude Code Built My Entire Job Search Automation in 35 Minutes"
- "From Zero to Job Search AI — Live Coding with Claude Code"

---

## ACT 1: THE HOOK + SETUP (0:00 - 5:00)

### Scene 1 — The Problem (0:00 - 2:00)
**On screen**: Messy spreadsheet with 20+ job listings, no structure

**Dhaval**: "You're applying to jobs. 30 tabs open — JDs, LinkedIn, your resume. Copy-pasting into a spreadsheet. There has to be a better way, right?"

**You**: "What if we could build a tool that reads your resume, scores how well you match each job, finds people to reach out to at the company, AND writes personalized LinkedIn messages — all automatically?"

**Dhaval**: "And you're going to build this from scratch? Right now?"

**You**: "Not just me — me and Claude Code."

### Scene 2 — Demo the Finished Tool (2:00 - 3:30)
**On screen**: Finished Excel tracker — color-coded match scores, referral names, LinkedIn URLs, personalized messages

Walk through one completed row: "Green = 70%+ match. It found 3 people. And these messages mention MY actual skills — not generic templates."

> **Why**: Show the destination before the journey. Audience knows what they're building toward.

### Scene 3 — Project Setup with Claude Code (3:30 - 5:00)
**On screen**: Terminal
```bash
mkdir jobsearch && cd jobsearch && git init
claude   # launch Claude Code
```

**Dhaval**: "So you just type `claude` and it starts?"

**Claude Code prompt**: *"I want to build a Python project that: 1) parses my resume PDF, 2) matches it against job descriptions, 3) finds LinkedIn referrals at target companies, 4) generates personalized outreach messages, 5) tracks everything in Excel. Set up the project structure with config.py, requirements.txt, .env.example, and .gitignore."*

**Claude Code magic moment**: Creates 4 files at once — config.py, requirements.txt, .env.example, .gitignore. Point out it asks for permission before writing.

**Teaching**: First taste of Claude Code. One prompt = multiple production files.

---

## ACT 2: BUILDING THE CORE (5:00 - 19:00)

### Scene 4 — Shared Claude API Client (5:00 - 9:00)

**Dhaval**: "Our tool needs to talk to the Claude API multiple times. But we don't want to repeat API-calling code in every file, right?"

**Claude Code prompt**: *"Create claude_client.py with: a singleton Anthropic client, a function to call Claude with retry logic, a helper to extract JSON from responses that might be wrapped in markdown code blocks, and a convenience function that calls Claude and parses as JSON."*

**Walk through 3 key patterns**:
1. **Singleton** — one client for the whole app
2. **JSON extraction** — Claude sometimes wraps JSON in ```json blocks; this strips it
3. **Retry logic** — automatic backoff on API errors

**Dhaval's dumb question**: "Why do we need JSON extraction? Can't we just ask Claude to return JSON?"
**You**: "Claude sometimes wraps it in markdown code blocks — this is a common gotcha."

### Scene 5 — Resume Parser (9:00 - 14:00)
> **This is the first BIG "wow" moment** — ~199 lines generated in one shot

**Dhaval**: "We need to read a PDF resume and extract skills, experience, education. This could take an afternoon by hand."

**Claude Code prompt**: *"Create resume_parser.py that: extracts text from PDF using pdfplumber, uses regex and keyword matching to extract skills (comprehensive tech skill list), years of experience, education, certifications, projects, and tools. Include caching so we don't re-parse the same PDF every run."*

**On screen**: Watch ~199 lines appear — skill keywords list, regex patterns, caching logic.

**Walk through key sections**:
- PDF text extraction with pdfplumber
- Skills = keyword matching (list of 50+ tech terms)
- Experience = regex for year ranges, with fallbacks
- Caching = stores parsed JSON, checks file modification time

**Dhaval's dumb question**: "Why keyword matching instead of asking Claude to extract skills?"
**You**: "Keyword matching is free and instant. We save Claude API calls for things that actually need intelligence — like matching and messages."

**Quick test**: Drop a resume PDF in `resume/`, run the parser, show structured output.

### Scene 6 — JD Parser (14:00 - 17:00)

**Dhaval**: "Now the other half — job descriptions. But JDs are all formatted differently..."

**Claude Code prompt**: *"Create jd_parser.py that takes raw job description text and uses our claude_client to extract: job_title, company_name, location, required_skills, preferred_skills, experience_required, key_responsibilities (max 5), and domain. Return structured JSON."*

**Highlight the prompt engineering**:
- "Return ONLY valid JSON" — crucial, prevents Claude from adding commentary
- Exact field types specified
- Defaults for every field (defensive coding against missing keys)

**Teaching**: "When to use AI vs regex. JDs are too varied for regex — this is where AI shines. And notice the file is only ~44 lines. Sometimes the AI-powered solution is LESS code."

### Scene 7 — Quick Test (17:00 - 19:00)
**You**: Set up `.env` with API key, `pip install -r requirements.txt`
**Dhaval**: "Where do people get the API key?"
**You**: Brief walkthrough — console.anthropic.com, .env.example as template

Paste a sample JD, run parser, show the structured JSON output.

---

## ACT 3: THE SMART STUFF (19:00 - 30:00)

### Scene 8 — Resume-JD Matcher (19:00 - 23:00)
> **The core value of the tool**

**Dhaval**: "We can read resumes AND job descriptions. Now — how good is the match?"

**Claude Code prompt**: *"Create matcher.py that compares resume to JD using Claude. Score 0-100 based on: skills overlap (40% weight), experience fit (25%), project relevance (20%), education & certs (15%). Return 3 specific, actionable improvement suggestions. Validate and clamp percentage between 0-100."*

**Highlight prompt engineering**:
- Weighted criteria make scores consistent and explainable
- "specific, actionable" improvements vs generic advice
- Few-shot example in the prompt (showing the FORMAT you want)
- `max(0, min(100, ...))` clamping pattern

**Dhaval's dumb question**: "Would Claude really return 150%?"
**You**: "Probably not, but defensive coding with LLMs is about handling the unexpected. One line of code prevents downstream bugs."

**Quick test**: Match sample resume against sample JD, show score + improvements.

### Scene 9 — Referral Finder (23:00 - 27:00)
> **The most "practically impressive" module for viewers**

**Dhaval**: "This saves people HOURS. For every job, find real LinkedIn profiles to reach out to."

**Claude Code prompt**: *"Create referral_finder.py. Find 3 LinkedIn profiles at a company. Use SerpAPI if configured (more reliable), fall back to googlesearch-python. Search for three types: same role, hiring manager, peer engineer. Handle rate limiting. If <3 profiles found, include manual Google search link as fallback."*

**Walk through**:
- 3 targeted searches (same_role, hiring_manager, peer) — strategic, not random
- `site:linkedin.com/in` Google operator — teach this!
- Dual backends: SerpAPI (reliable, free 100/month) vs Google (free but rate-limited)
- Graceful degradation: can't find someone? Here's a manual search link

**Dhaval**: "This module has ZERO Claude API calls — it uses traditional web search. Not everything needs AI."

### Scene 10 — Message Generator (27:00 - 30:00)

**Dhaval**: "We have profiles. Now we write personalized cold messages."

**Claude Code prompt**: *"Create message_generator.py. Generate personalized LinkedIn connection messages (~280 chars) for each referral. Batch all into a single Claude API call. Be specific, not generic, not desperate — reference actual skills and projects. Handle placeholder referrals with N/A."*

**Highlight the prompt rules baked in**:
- "Do NOT be generic" / "Do NOT be needy"
- "End with a soft ask (learn about their experience, not 'please refer me')"
- 280 char limit = LinkedIn connection request limit

**The optimization**: 3 messages in ONE API call instead of 3 separate calls = 66% fewer API calls.

**Read a sample message aloud** — show it's specific, professional, human-sounding.

---

## ACT 4: TYING IT TOGETHER (30:00 - 37:00)

### Scene 11 — Excel Handler (30:00 - 33:00)

**Claude Code prompt**: *"Create excel_handler.py using openpyxl. 10 columns: job link, JD text, match %, improvements, 3x referral+message pairs. Auto-create tracker if missing. Color-code match % (green >=70, yellow >=50, red <50). Context manager for batch writes. Save after each row."*

**Walk through**:
- Color coding with PatternFill (green/yellow/red)
- `TrackerWriter` context manager pattern
- Permission check before processing (don't waste API credits if file is locked!)
- Column migration for backward compatibility

**Dhaval's dumb question**: "What's a context manager?"
**You**: "`__enter__` runs at start, `__exit__` runs at end — even if there's a crash. Guarantees the Excel file gets closed properly."

### Scene 12 — Main Orchestrator (33:00 - 35:00)

**Claude Code prompt**: *"Create main.py that orchestrates the full pipeline: validate API key, read unprocessed rows from Excel, parse resume once (cached), then for each row: parse JD -> match -> find referrals -> generate messages -> write to Excel. Delays between API calls. Print summary at the end."*

**Show the clean pipeline**:
```
For each job posting:
  1. parse_jd(jd_text)           -> structured JD data
  2. match_resume_to_jd(...)     -> match % + improvements
  3. find_referrals(...)         -> 3 LinkedIn profiles
  4. generate_messages(...)      -> 3 personalized messages
  5. writer.write_results(...)   -> save to Excel
```

**Teaching**: "Look how clean this reads. Each step calls one module. main.py is just the conductor. This is the payoff of modular code."

### Scene 13 — THE LIVE DEMO (35:00 - 37:00)
> **Energy: HIGHEST. Let it breathe.**

**Setup**:
1. Show `.env` has a valid API key (mask it on screen)
2. Resume PDF in `resume/`
3. Open Excel tracker — 2 rows with job links + JD text pasted, everything else empty
4. Close Excel (important — tool checks for this!)

**Run**: `python main.py`

**Watch terminal output live**:
```
Found 2 unprocessed job(s)...
Parsing resume... 18 skills, ~4 years experience
Processing row 2: Senior Data Engineer at Stripe — 72% match
  Found 3 referrals, generated 3 messages. Saved.
Processing row 3: Data Engineer at Airbnb — 65% match
  ...
```

**Switch to Excel**: Show completed rows — green 72%, yellow 65%, names, URLs, messages.

**Read one message aloud**: Show it's specific, warm, references real skills.

---

## ACT 5: WRAP UP (37:00 - 40:00)

### Scene 14 — Recap + What You Learned

**Architecture diagram overlay**:
```
Resume (PDF) -----> resume_parser.py --+
                                       |
Job Description --> jd_parser.py ------+--> matcher.py --> % + tips
                                       |
                                       +--> referral_finder.py --> profiles
                                       |
                                       +--> message_generator.py --> messages
                                       |
                                       v
                                  excel_handler.py --> Tracker.xlsx
```

**You**: "9 Python files. ~1000 lines of production code. Built in one session with Claude Code."

**Claude Code takeaways**:
1. It makes architectural decisions (shared client, caching, fallbacks)
2. It writes complete modules — not toy snippets
3. It handles edge cases you didn't ask for
4. You still need to understand what it builds — review, test, iterate

**Extension ideas**: Auto-apply via APIs, email outreach, dashboard instead of Excel, resume tailoring per job.

**Dhaval**: "Link to the repo in the description. Go build something."

---

## Quick Reference Tables

### Dhaval's "Dumb Questions" (what beginners need answered)
| Question | Scene | Concept |
|----------|-------|---------|
| "What exactly IS Claude Code?" | 3 | Tool intro |
| "Why keyword matching instead of Claude for skills?" | 5 | Cost/speed tradeoffs |
| "Why do we need JSON extraction?" | 4 | LLM output quirks |
| "Would Claude really return 150%?" | 8 | Defensive programming |
| "What's a context manager?" | 11 | Python fundamentals |
| "We have to CLOSE Excel first?" | 13 | File locking |

### Claude Code "Magic" Moments
| Scene | Moment | Why it impresses |
|-------|--------|-----------------|
| 3 | Creates 4 project files at once | Speed + structure |
| 5 | 199 lines of resume parser in one shot | Scale of generation |
| 4 | Anticipates shared client need | Architectural thinking |
| 8 | Sophisticated weighted scoring prompt | Prompt engineering |
| 9 | Builds 3-tier search + fallback chain | Strategic edge cases |
| 10 | Batches 3 API calls into 1 | Cost optimization |
| 11 | Adds color coding unprompted | UX polish |

### Pacing Guide
| Scene | Energy | Speed | Viewer emotion |
|-------|--------|-------|---------------|
| 1-2 (Hook + Demo) | HIGH | Fast | "I want that!" |
| 3 (Setup) | Medium | Measured | Learning |
| 4-5 (Client + Resume) | HIGH | Slow for explanations | First "wow" |
| 6-7 (JD + Test) | Medium | Moderate | Understanding |
| 8 (Matcher) | HIGH | Slow for teaching | "This is clever" |
| 9 (Referrals) | HIGH | Moderate | "This saves hours!" |
| 10 (Messages) | Medium | Moderate | Appreciating craft |
| 11-12 (Excel + Main) | Medium | Faster | "Almost there" |
| 13 (Live Demo) | HIGHEST | Let it breathe | PAYOFF |
| 14 (Wrap) | Medium-High | Measured | Inspired |

### If Running Long (>45 min) — Cut:
- Scene 11 (Excel): Show color-coding only, skip column width details
- Scene 4 (Client): Shorten singleton explanation to one sentence
- Scene 12 (Main): Flash the pipeline list, move on

### If Running Short (<30 min) — Extend:
- After Scene 9: Live-test just the referral finder, show real LinkedIn URLs appearing
- Scene 13: Process 3 jobs instead of 2, read multiple messages aloud

### Production Notes
- **Screen layout**: Terminal (Claude Code) 60% left, file preview 40% right. Switch to Excel for demos.
- **Pre-record tip**: Do a dry run first. Keep moments where Claude Code needs extra prompting — they're authentic and educational.
- **Thumbnail**: Split screen — messy job search spreadsheet on left, clean color-coded AI tracker on right.

### Files Built (tutorial order)
1. `config.py` — Configuration + paths
2. `requirements.txt` — Dependencies
3. `.env.example` — API key template
4. `.gitignore` — Ignore patterns
5. `claude_client.py` — Shared API client (singleton)
6. `resume_parser.py` — PDF extraction + caching (~199 lines)
7. `jd_parser.py` — AI-powered JD parsing (~44 lines)
8. `matcher.py` — Weighted resume-JD scoring (~53 lines)
9. `referral_finder.py` — LinkedIn profile discovery (~194 lines)
10. `message_generator.py` — Personalized outreach (~105 lines)
11. `excel_handler.py` — Excel tracker with formatting (~218 lines)
12. `main.py` — Pipeline orchestrator (~139 lines)
