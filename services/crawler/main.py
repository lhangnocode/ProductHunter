from pathlib import Path
import time

from services.crawler.core.storage.database_handler import DatabaseHandler
from services.crawler.core.storage.typesense_handler import TypesenseHandler
from services.crawler.impl.fpt.crawler_fptshop import FptTrojanPro
from services.crawler.impl.phongvu.crawler_phongvu import PhongVuCrawler


BASEOUTPUT_DIR = Path(__file__).resolve().parent / "output"


def _check_database() -> bool:
    db = DatabaseHandler()
    try:
        db.query("SELECT 1")
        return True
    except Exception as exc:
        print(f"[!] Database unavailable: {exc}")
        return False
    finally:
        db.close_connection()


def _check_typesense() -> bool:
    typesense = TypesenseHandler()
    try:
        typesense.ensure_collection()
        return True
    except Exception as exc:
        print(f"[!] Typesense unavailable: {exc}")
        return False


def _wait_for_dependencies(max_attempts: int = 5, delay_seconds: int = 5) -> bool:
    for attempt in range(1, max_attempts + 1):
        db_ready = _check_database()
        ts_ready = _check_typesense()
        if db_ready and ts_ready:
            return True
        if attempt < max_attempts:
            print(f"[!] Dependencies not ready (attempt {attempt}/{max_attempts}). Retrying in {delay_seconds}s...")
            time.sleep(delay_seconds)
    return False


def main() -> None:
    if not _wait_for_dependencies():
        raise SystemExit("[!] Dependencies unavailable. Aborting crawl run.")
    fpt_crawler = FptTrojanPro(output_dir=str(BASEOUTPUT_DIR))
    fpt_crawler.crawl()

    phongvu_crawler = PhongVuCrawler(output_dir=str(BASEOUTPUT_DIR))
    phongvu_crawler.crawl()


if __name__ == "__main__":
    main()
