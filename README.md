# PythonScraper

The "Search-Engine-and-Crawler" folder was cloned from divyanshch: https://github.com/divyanshch/Search-Engine-and-Crawler.
The original crawler can be found in crawler.py
crawlerExpand.py separates tasks into functions, implements logging, URL-cleaning etc.
crawlerNoBS.py utilizes simple string searches instead of the BeautifulSoup library to find new links

The "Scraper" folder utilizes the same principles as the crawler but combines it with a string search on pages in a single web domain to output a result of searching for keywords instead of saving all pages it encounters.
