from src.scrapers.base import BaseScraper
from src.scrapers.indeed import IndeedScraper
from src.scrapers.remoteok import RemoteOKScraper
from src.scrapers.rss import WeWorkRemotelyScraper
from src.scrapers.linkedin import LinkedInScraper
from src.scrapers.indian_jobs import HiristScraper, AmbitionBoxScraper, BuiltInScraper
from src.scrapers.jobsora import JobsoraScraper
from src.scrapers.jooble import JoobleScraper


def get_enabled_scrapers(settings: dict) -> list[BaseScraper]:
    scrapers: list[BaseScraper] = []
    scraper_config = settings.get("scrapers", {})

    if scraper_config.get("indeed", {}).get("enabled", False):
        scrapers.append(IndeedScraper(scraper_config["indeed"]))

    if scraper_config.get("remoteok", {}).get("enabled", False):
        scrapers.append(RemoteOKScraper(scraper_config["remoteok"]))

    if scraper_config.get("weworkremotely", {}).get("enabled", False):
        scrapers.append(WeWorkRemotelyScraper(scraper_config["weworkremotely"]))

    if scraper_config.get("linkedin", {}).get("enabled", False):
        scrapers.append(LinkedInScraper(scraper_config["linkedin"]))

    if scraper_config.get("hirist", {}).get("enabled", False):
        scrapers.append(HiristScraper(scraper_config["hirist"]))

    if scraper_config.get("ambitionbox", {}).get("enabled", False):
        scrapers.append(AmbitionBoxScraper(scraper_config["ambitionbox"]))

    if scraper_config.get("builtin", {}).get("enabled", False):
        scrapers.append(BuiltInScraper(scraper_config["builtin"]))

    if scraper_config.get("jobsora", {}).get("enabled", False):
        scrapers.append(JobsoraScraper(scraper_config["jobsora"]))

    if scraper_config.get("jooble", {}).get("enabled", False):
        scrapers.append(JoobleScraper(scraper_config["jooble"]))

    return scrapers
