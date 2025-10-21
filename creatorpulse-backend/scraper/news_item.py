from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class NewsItem:
    """A structured representation of a scraped news item or article."""

    title: str
    url: str
    source: str
    published_at: Optional[datetime] = None
    summary: Optional[str] = None
    image_url: Optional[str] = None
    score: float = field(default=0.0)
