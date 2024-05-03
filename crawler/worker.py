from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time


class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)
        
    def run(self):
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")

                '''check this part!!!'''
                unique_page_count = len(scraper.unique_urls)  # Count unique URLS
                longest_page = scraper.longest_page
                max_word_count = scraper.max_word_count
                fifty_common_words = scraper.word_freq.most_common(50)
                subdomain_pages = scraper.subdomain_pages
                #num_similar_page = scraper.similar_page_count

                print(f"There are {unique_page_count} unique pages.")
                print(f"The longest page in terms of words is {longest_page}, with {max_word_count} words.")
                print("The 50 most common words in the entire set of pages are: ", fifty_common_words)
                print("Subdomains:")
                for subdomain, pages in subdomain_pages.items():
                    print(f"{subdomain}, {len(pages)}")
                #print(f"There are {num_similar_page} pages that have similar information or no information.")


                break
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            scraped_urls = scraper.scraper(tbd_url, resp)
            for scraped_url in scraped_urls:
                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
