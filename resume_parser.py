"""Parses resume PDF into structured data with caching."""

import json
import os
import re

import config


def _extract_text_from_pdf(pdf_path: str) -> str:
    """Extract all text from a PDF file."""
    import pdfplumber

    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def _extract_skills(text: str) -> list[str]:
    """Extract skills from resume text by looking for common skill patterns."""
    skills = []
    skill_keywords = [
        "Python", "SQL", "PySpark", "Spark", "Java", "Scala", "R",
        "JavaScript", "TypeScript", "Go", "Rust", "C++", "C#",
        "Airflow", "Luigi", "Prefect", "Dagster",
        "AWS", "GCP", "Azure", "S3", "EC2", "Lambda", "Glue", "Redshift",
        "BigQuery", "Dataflow", "Cloud Functions",
        "Snowflake", "Databricks", "dbt",
        "Kafka", "RabbitMQ", "Kinesis", "Pub/Sub",
        "Docker", "Kubernetes", "Terraform", "CI/CD",
        "PostgreSQL", "MySQL", "MongoDB", "Cassandra", "DynamoDB", "Redis",
        "Hadoop", "Hive", "MapReduce", "HDFS",
        "Tableau", "Power BI", "Looker", "Metabase",
        "Git", "GitHub", "GitLab", "Jira",
        "ETL", "ELT", "Data Warehouse", "Data Lake",
        "Machine Learning", "Deep Learning", "NLP", "TensorFlow", "PyTorch",
        "Pandas", "NumPy", "Scikit-learn", "Matplotlib",
        "REST", "GraphQL", "API", "Microservices",
        "Linux", "Shell", "Bash",
    ]
    text_lower = text.lower()
    for skill in skill_keywords:
        if skill.lower() in text_lower:
            skills.append(skill)
    return list(set(skills))


def _extract_experience_years(text: str) -> str:
    """Estimate years of experience from resume text."""
    patterns = [
        r"(\d+)\+?\s*years?\s*(?:of\s+)?experience",
        r"experience\s*:?\s*(\d+)\+?\s*years?",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1) + " years"

    # Look for date ranges in experience section to estimate
    year_pattern = r"20\d{2}"
    years = [int(y) for y in re.findall(year_pattern, text)]
    if years:
        span = max(years) - min(years)
        if span == 0:
            return "<1"
        return f"~{span} years"
    return "<1"


def _extract_education(text: str) -> str:
    """Extract education information."""
    edu_patterns = [
        r"(B\.?Tech|B\.?E\.?|B\.?S\.?|M\.?Tech|M\.?S\.?|M\.?E\.?|Ph\.?D\.?|MBA)[^,\n]*(?:in\s+)?[^,\n]*",
        r"(Bachelor|Master|Doctor)[^,\n]*",
    ]
    for pattern in edu_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return ""


def _extract_certifications(text: str) -> list[str]:
    """Extract certifications from resume text."""
    certs = []
    cert_keywords = [
        "certified", "certification", "certificate", "credential",
        "AWS Certified", "Google Cloud", "Azure", "Databricks",
        "Snowflake", "Confluent", "Coursera", "Udemy",
    ]
    lines = text.split("\n")
    for line in lines:
        line_lower = line.lower()
        for keyword in cert_keywords:
            if keyword.lower() in line_lower and len(line.strip()) > 10:
                certs.append(line.strip())
                break
    return list(set(certs))


def _extract_projects(text: str) -> list[str]:
    """Extract project names from resume text."""
    projects = []
    lines = text.split("\n")
    in_projects_section = False
    for line in lines:
        line_stripped = line.strip()
        if re.match(r"(?:projects?|personal projects?|key projects?)", line_stripped, re.IGNORECASE):
            in_projects_section = True
            continue
        if in_projects_section:
            if re.match(r"(?:experience|education|skills|certifications?|awards?)", line_stripped, re.IGNORECASE):
                in_projects_section = False
                continue
            if line_stripped and len(line_stripped) > 5:
                # Take the first part as project name (before any dash or pipe)
                name = re.split(r"\s*[|–—-]\s*", line_stripped)[0].strip()
                if name and len(name) > 3:
                    projects.append(name)
    return projects[:10]  # Limit to 10 projects


def _extract_tools(text: str) -> list[str]:
    """Extract tools/technologies mentioned in the resume."""
    tools = [
        "Airflow", "AWS S3", "Snowflake", "BigQuery", "Databricks",
        "Docker", "Kubernetes", "Terraform", "Jenkins", "GitHub Actions",
        "dbt", "Spark", "Kafka", "Tableau", "Power BI", "Looker",
        "Jupyter", "VS Code", "IntelliJ", "DataGrip",
        "Postman", "Swagger", "Grafana", "Prometheus",
        "Celery", "Redis", "Elasticsearch", "Nginx",
    ]
    found = []
    text_lower = text.lower()
    for tool in tools:
        if tool.lower() in text_lower:
            found.append(tool)
    return list(set(found))


def _truncate_text(text: str, max_tokens: int = 2000) -> str:
    """Truncate text to approximately max_tokens (rough estimate: 1 token ~ 4 chars)."""
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n[... truncated for token efficiency ...]"


def parse_resume(resume_path: str = None) -> dict:
    """
    Parse resume PDF and return structured data.
    Uses caching to avoid re-parsing if PDF hasn't changed.
    """
    if resume_path is None:
        resume_path = config.RESUME_PATH

    if not os.path.exists(resume_path):
        raise FileNotFoundError(
            f"Resume PDF not found at: {resume_path}\n"
            f"Please place your resume PDF at this path."
        )

    cache_path = config.PARSED_RESUME_CACHE
    pdf_mtime = os.path.getmtime(resume_path)

    # Check cache
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            cached = json.load(f)
        if cached.get("_pdf_mtime") == pdf_mtime:
            return cached

    # Parse fresh
    raw_text = _extract_text_from_pdf(resume_path)
    if not raw_text:
        raise ValueError(f"Could not extract text from resume PDF: {resume_path}")

    parsed = {
        "raw_text": _truncate_text(raw_text),
        "skills": _extract_skills(raw_text),
        "experience_years": _extract_experience_years(raw_text),
        "education": _extract_education(raw_text),
        "certifications": _extract_certifications(raw_text),
        "projects": _extract_projects(raw_text),
        "tools": _extract_tools(raw_text),
        "_pdf_mtime": pdf_mtime,
    }

    # Cache to disk
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(parsed, f, indent=2)

    return parsed
