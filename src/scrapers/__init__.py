from src.scrapers.base import BaseScraper
from src.scrapers.indeed import IndeedScraper
from src.scrapers.remoteok import RemoteOKScraper
from src.scrapers.rss import WeWorkRemotelyScraper


def get_enabled_scrapers(settings: dict) -> list[BaseScraper]:
    scrapers: list[BaseScraper] = []
    scraper_config = settings.get("scrapers", {})

    if scraper_config.get("indeed", {}).get("enabled", False):
        scrapers.append(IndeedScraper(scraper_config["indeed"]))

    if scraper_config.get("remoteok", {}).get("enabled", False):
        scrapers.append(RemoteOKScraper(scraper_config["remoteok"]))

    if scraper_config.get("weworkremotely", {}).get("enabled", False):
        scrapers.append(WeWorkRemotelyScraper(scraper_config["weworkremotely"]))

    return scrapers
