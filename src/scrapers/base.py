from abc import ABC, abstractmethod

from src.models import ScrapeResult


class BaseScraper(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def scrape(self) -> ScrapeResult:
        ...
