from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional


class Crawler(ABC):
    """Base abstract class for all crawlers."""

    def __init__(self, name: str, output_dir: str, base_url: Optional[str] = None) -> None:
        self.name = name
        self.output_dir = output_dir
        self.base_url = base_url

    @abstractmethod
    def crawl(self) -> None:
        raise NotImplementedError("Subclasses must implement this method")
