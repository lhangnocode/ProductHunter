from pathlib import Path

from services.crawler.impl.fpt.crawler_fptshop import FPTShopCrawler
from services.crawler.impl.phongvu.crawler_phongvu import PhongVuCrawler


BASEOUTPUT_DIR = Path(__file__).resolve().parent / "output"


def main() -> None:
    # fpt_crawler = FPTShopCrawler(output_dir=str(BASEOUTPUT_DIR))
    # fpt_crawler.crawl()

    phongvu_crawler = PhongVuCrawler(output_dir=str(BASEOUTPUT_DIR))
    phongvu_crawler.crawl()


if __name__ == "__main__":
    main()
