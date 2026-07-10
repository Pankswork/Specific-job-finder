from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class JobPost:
    title: str
    company: str
    location: str
    url: str
    source: str
    description: str
    salary: Optional[str] = None
    posted_date: Optional[str] = None
    scraped_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def fingerprint(self) -> str:
        return f"{self.company}::{self.title}::{self.location}"


@dataclass
class ScoredJob:
    job: JobPost
    score: int
    reasoning: str
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)


@dataclass
class ScrapeResult:
    source: str
    jobs: list[JobPost]
    errors: list[str] = field(default_factory=list)


@dataclass
class RunSummary:
    total_found: int
    new_jobs: int
    scored: int
    notified: int
    errors: list[str] = field(default_factory=list)
    scored_jobs: list[ScoredJob] = field(default_factory=list)
