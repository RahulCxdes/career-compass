
from enum import Enum
from typing import Literal


class QueryTarget(str, Enum):
    RESUME = "resume"
    JD = "jd"
    BOTH = "both"
    UNKNOWN = "unknown"


RESUME_KEYWORDS = [
    "my resume", "resume", "cv", "profile", "improve my", "fix my",
    "update resume", "improve summary", "improve my summary",
]

JD_KEYWORDS = [
    "jd", "job description", "job role", "backend role", "frontend role",
    "am i ready for", "requirements for", "skills for",
]

BOTH_KEYWORDS = [
    "compare", "match", "difference", "gap", "missing",
    "skills i lack", "what am i missing",
]


def detect_query_target(query: str) -> QueryTarget:
    """Classify the user query as resume / jd / both / unknown."""
    q = query.lower()

    if any(kw in q for kw in BOTH_KEYWORDS):
        return QueryTarget.BOTH

    resume_hit = any(kw in q for kw in RESUME_KEYWORDS)
    jd_hit = any(kw in q for kw in JD_KEYWORDS)

    if resume_hit and jd_hit:
        return QueryTarget.BOTH
    if resume_hit:
        return QueryTarget.RESUME
    if jd_hit:
        return QueryTarget.JD

    return QueryTarget.UNKNOWN


def target_for_retrieval(query: str) -> QueryTarget:
    """
    Apply your rule:
      - classify with detect_query_target
      - if UNKNOWN → default to RESUME for retrieval
    """
    target = detect_query_target(query)
    if target == QueryTarget.UNKNOWN:
        return QueryTarget.RESUME
    return target
