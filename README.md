# PythonScraper

The "Search-Engine-and-Crawler" folder was cloned from divyanshch: https://github.com/divyanshch/Search-Engine-and-Crawler.
The original crawler can be found in crawler.py
crawlerExpand.py separates tasks into functions, implements logging, URL-cleaning etc.
crawlerNoBS.py utilizes simple string searches instead of the BeautifulSoup library to find new links

~~The "Scraper" folder utilizes the same principles as the crawler but combines it with a string search on pages in a single web domain to output a result of searching for keywords instead of saving all pages it encounters.~~ The "Scraper" folder has migrated and the scripts have been moved to the root of the repository i.e. here.

## Setting up python environment
```
virtualenv -p python3.5 env3.5
```

## Requirements
```
pip install requests
pip install bs4
pip install tldextract
pip install html5
pip install pandas
pip install tqdm
```

### keywords
Create a `keywords.txt` file on this directory with a list of keywords to look for. Each keyword is on a new line.

## Organization

There are two scripts. The `crawler.py` and `search.py`.


### crawlerExpand.py

This script collects pages from the given website and stores them locally on your
machine.

#### Sample usage
```
python crawlerExpand.py [URL] 10 50 myuni
```

### search.py

This script allows you to search the pages you have collected above using keywords
and generates a Comma Separated Values (CSV) file with all the keywords found,
their frequency and sorted.

#### Sample usage
```
./search.py -f myuni -k keywords_game.txt
```

####  Help documentation
```
./search.py -h
```
