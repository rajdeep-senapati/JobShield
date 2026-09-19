from dataclasses import dataclass, field
from typing import List


@dataclass
class Job:
    title: str
    company: str
    location: str = ""
    description: str = ""
    skills: List[str] = field(default_factory=list)
    employment_type: str = ""
    source: str = ""
    url: str = ""
