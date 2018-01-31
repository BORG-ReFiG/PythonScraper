#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import sys
import re
import urllib.parse
import logging
import os
import time
import codecs
import requests
import string
from bs4 import BeautifulSoup
import tldextract
try:
    from os import scandir, walk
except ImportError:
    from scandir import scandir, walk
from tqdm import tqdm
import validators
import grequests
from tld import get_tld
from tld.utils import update_tld_names

# update_tld_names() https://stackoverflow.com/a/22228140
logger = logging.getLogger(__name__)

# current time, used in the names of the folder and the logging file
curtime = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
# Create a new log file
logging.basicConfig(filename=('_uniscraperlog_' + curtime + '.log'),
                    level=logging.DEBUG
                    )

# https://github.com/tqdm/tqdm/issues/481
tqdm.monitor_interval = 0

# RegEx that is used to filter searches for URLs on any given page.
# Used in is_relevant_link_from_soup and is_relevant_link_from_html functions
filter_regex = re.compile(".*([Pp]rogram|[Aa]dmission|[Cc]ertificate|[Dd]egree|[Dd]iploma|[Ff]aculty|[Ss]chool|[Dd]epartment|[Uu]ndergrad|[Gr]rad|[Ss]chool).*")
filter_title_regex = re.compile(".*([Pp]rogram|[Aa]dmission|[Cc]ourse).*")

def main():

    current_working_dir = os.getcwd()  # current directory we are standing on

    websites_list = get_file_content_as_list(websites_file)

    overall_prog = tqdm(total=len(websites_list), unit="website", desc="Overall")
    for idx, website in enumerate(websites_list):
        planned_urls_array = []
        crawled_urls_array = []

        # Extracts the top level domain from the URL (eg. ualberta.ca, no slashes)
        seed = tldextract.extract(website).domain

        pbar = {}
        pbar[idx] = tqdm(total=max_pages, unit="page", desc=website)
        if validators.url(website):
            batch_website = "{}_{}".format(batch_name, get_tld(website))
            if not os.path.exists(batch_website):
                os.mkdir(batch_website)
                with ChDir(batch_website):
                    setup_crawler_files()
                start_page = 1
            else:
                with ChDir(batch_website):
                    start_page = get_start_page()

            with ChDir(batch_website):
                crawl(seed, pbar[idx], start_page, planned_urls_array, crawled_urls_array, website, max_pages)
        overall_prog.update(1)

def crawl(seed, prog_upd, start_page, planned_urls_array, crawled_urls_array, website, max_pages):
    """Function that takes link, saves the contents to text file call href_split
    """
    logging.info("Crawling through domain '" + seed + "'")
    tqdm.write("++++++++++Crawling through domain {}+++++++++++".format(seed))
    visited_urls, planned_urls, crawled_urls = setup_crawler_files()

    if start_page == 1:

        # Array that holds the queue to be visited later
        planned_urls_array.append(website)
        # Logging the urls
        planned_urls.write(website)
        planned_urls.write("\n")

        # Gets the root of the url
        url_split = website.split("://", 1)
        # Array that holds urls that have been found.
        # This is the array that all new URLs are checked against to prevent repeating.
        # Record URL with both http and https prefixes
        crawled_urls_array.append("http://" + url_split[1])
        crawled_urls_array.append("https://" + url_split[1])
        # Also log the same into the text file
        crawled_urls.write("http://" + url_split[1] + "\n")
        crawled_urls.write("https://" + url_split[1] + "\n")

    while start_page <= max_pages and len(planned_urls_array) > 0:
        start_page = process_current_link(start_page,
                                          prog_upd,
                                          planned_urls_array[0],
                                          seed,
                                          visited_urls,
                                          crawled_urls_array,
                                          crawled_urls,
                                          planned_urls_array,
                                          planned_urls,
                                          max_pages,
                                         )
        prog_upd.update(1)

        # Deletes the currently looked at URL from the queue
        planned_urls_array.pop(0)


def process_current_link(page, prog_upd, link, seed, visited_urls, crawled_urls_array, crawled_urls, planned_urls_array, planned_urls, max_pages):
    """Function that grabs the first link in the
    list of planned urls, requests the page and processes it
    """
    empty_request_log = codecs.open("_empty_requests.txt", "w", "utf-8")

    # Try to get the html of the URL
    r = request_url(link, visited_urls)

    grab_all = False
    if r:  # if the request returned an html
        html = r.text
        current_url = r.url
        # Soupify
        # For now it soupifies the link regardless of the mode,
        # because it uses soup later to extract visible text from the page
        soup = BeautifulSoup(html, 'html.parser')
        grab_all = is_title_page_relevant(soup)

        # Gets the name for the file to store the html text in
        name = create_name_from_html(html)

        # find and process all links
        process_links_from_html(html,
                                prog_upd,
                                current_url,
                                seed,
                                crawled_urls_array,
                                crawled_urls,
                                planned_urls_array,
                                planned_urls,
                                grab_all,
                                )

        # Adds the .txt to the end of the name
        name = "{0}.txt".format(name)

        # Find only visible text
        visible_text = extract_text(soup)

        if visible_text:  # save it as a text file
            try:
                # Create and open the file with that name
                fo = codecs.open(name, "w", "utf-8-sig")
                # Write URL to that file
                fo.write(current_url + "\n")
                # Append the html to the file
                fo.write(visible_text)
                # Close the pipe to the file
                fo.close()
                # Log the creation of the file
                logging.info('Created file ' + name)

            except KeyboardInterrupt:
                tqdm.write("Script interrupted by user. Shutting down.")
                logging.info("Script interrupted by user")
                shut_down()
            except Exception:
                logging.exception("Can not encode file: " + current_url)
        else:
            tqdm.write("No visible text in {}".format(link))
            logging.warning('No visible text in ' + link)
    # Else: html does not exist or is empty. Log error
    else:
        logging.warning('Request for ' + link + ' returned empty html')
        empty_request_log.write(link)
        empty_request_log.write("\n")

    # Update on the total number of pages
    num_digits = len(str(max_pages))
    grab_blurb = "grabbing ALL links" if grab_all else "grabbing key links"
    tqdm.write("[{0:0{width}d}]:[{1}] – {2}".format(page, grab_blurb.ljust(18), link, width=num_digits))

    # Increment page count
    page += 1
    # Every 50 pages checks the size of the folder. Prints the amount of data collected in MB to the console and log file
    if page % 50 == 0:
        size_of_directory = get_tree_size(os.curdir) / 1000000
        tqdm.write("Size: {} MB".format(str(round(size_of_directory, 5))))
        logging.info("Size: " + str(round(size_of_directory, 5)) + "MB")
    # Time delay in seconds to prevent crashing the server
    time.sleep(.01)
    return page

def get_tree_size(path):
    """Return total size of files in given path and subdirs by going through the tree.
    Recursive.
    Called from main function
    """
    total = 0
    for entry in scandir(path):
        if entry.is_dir(follow_symlinks=False):
            total += get_tree_size(entry.path)
        else:
            total += entry.stat(follow_symlinks=False).st_size
    return total

def extract_links_from_page(html_page):
    return re.findall(r'<a href="(http[s]?://[^">]*)', html_page)

def process_links_from_html(html, prog_upd, cur_link, seed, crawled_urls_array, crawled_urls, planned_urls_array, planned_urls, grab_all=False):
    """Take an array of links, run the split on each and add the results
    to the appropriate arrays and files
    """
    links = []
    # tqdm.write("grabbing all {}".format(str(grab_all)))

    if html.partition('<body')[2]:
        html = html.partition('<body')[2]
    link_strings = html.split('href=') # split the page into sections using "href=" as a delimiter
    for lnk in link_strings[1:]:
        href = lnk.partition('</a')[0] # grab all text before the "</a" – this var now contains text after an href parameter and before a closing tag, and thus includes the text content of the link
        if (grab_all or is_relevant_link_from_html(href)):
            href = href.partition('>')[0]
            href = href.partition(' ')[0]
            href = dequote(href)
            new_link = (urllib.parse.urldefrag(href)[0]).rstrip('/')
            new_link = urllib.parse.urljoin(cur_link, new_link)
            if this_is_not_media(new_link):
                if check_domain(new_link, seed):
                    # if the link is not in crawledURLsArray then it appends it to urls and crawledURLsArray
                    if new_link not in crawled_urls_array:
                        # Ensures no jpg or pdfs are stored and that no mailto: links are stored.
                        if new_link.startswith("http") and '.pdf' not in new_link and '.jpg' not in new_link and '.mp3' not in new_link:
                            #???TODO: add checks for www.domain.com and https://
                            # Adds new link to array
                            planned_urls_array.append(new_link)
                            # Adds new link to queue file
                            planned_urls.write(new_link)
                            planned_urls.write("\n")

                            try:
                                # Remove the front of the URL (http or https)
                                http_split = new_link.split("://", 1)
                                # Add all possible link variations to file of URLs that have been looked at
                                # Adds new link to array
                                crawled_urls_array.append("http://" + http_split[1])
                                # Adds new link to already looked at file
                                crawled_urls.write("http://" + http_split[1])
                                crawled_urls.write("\n")
                                # Adds new link to array
                                crawled_urls_array.append("https://" + http_split[1])
                                # Adds new link to already looked at file
                                crawled_urls.write("https://" + http_split[1])
                                crawled_urls.write("\n")
                            except IndexError as e:
                                logging.info(str(e))

    return

def add_to_crawled_urls_list(new_link, crawled_urls_array, crawled_urls):
    """if the link is not in crawled_urls_array then it
    appends it to urls and crawled_urls_array
    """
    if new_link not in crawled_urls_array:
        # Ensures no jpg or pdfs are stored and that no mailto: links are stored.
        if new_link.startswith("http") and '.pdf' not in new_link and '.jpg' not in new_link and '.mp3' not in new_link:
            #???TODO: add checks for www.domain.com and https://
            try:
                # Remove the front of the URL (http or https)
                http_split = new_link.split("://", 1)
                # Add all possible link variations to file of URLs that have been looked at
                # Adds new link to array
                crawled_urls_array.append("http://" + http_split[1])
                # Adds new link to already looked at file
                crawled_urls.write("http://" + http_split[1])
                crawled_urls.write("\n")
                # Adds new link to array
                crawled_urls_array.append("https://" + http_split[1])
                # Adds new link to already looked at file
                crawled_urls.write("https://" + http_split[1])
                crawled_urls.write("\n")
            except IndexError as e:
                logging.info(str(e))

def add_to_planned_urls_list(new_link, planned_urls_array, planned_urls):
    # Adds new link to array
    planned_urls_array.append(new_link)
    # Adds new link to queue file
    planned_urls.write(new_link)
    planned_urls.write("\n")

def is_title_page_relevant(soup):
    return True if soup.find('title', string=filter_title_regex) else False

def this_is_not_media(new_link):
    path = urllib.parse.urlparse(new_link).path
    ext = os.path.splitext(path)[1]
    unwanted = ['.mp3', '.mp4', '.doc', '.docx', '.pdf', '.jpg', '.jpg', '.css']
    if ext not in unwanted and new_link.startswith("http"):
        return True
    else:
        return False

def create_name_from_html (html):
    """Function for creating name
    Use the title of the html page as the title of the text file
    Called from process_current_link
    Uses string search to locate the <title> tag
    Parameter html is a string
    """
    name_list = (html.partition("</title")[0]).split("<title") #grab part of html before </title
    name_part = name_list[-1] #grab part of html after <title
    name = name_part.split(">")[-1]
    if name:
        # removes invalid characters from title
        name = format_filename(name) + '__' + str(time.time())
        logging.info('Created name ' + name)
    else:
        name = "no_title_" + str(time.time()) # if no title provided give a no title with a timestamp
        logging.warn('Failed to create a name, using \'' + name + '\' instead')
    return name

def format_filename(name):
    #Taken from: https://gist.github.com/seanh/93666
    """Take a string and return a valid filename constructed from the string.
    Uses a whitelist approach: any characters not present in valid_chars are
    removed. Also spaces are replaced with underscores."""
    try:
        valid_chars = "-_() %s%s" % (string.ascii_letters, string.digits)
        filename = ''.join(c for c in name if c in valid_chars)
        # Remove spaces in filename
        filename = filename.strip()
        filename = filename.replace(' ','_')
    except TypeError as e:
        filename = str(uuid.uuid4())
        logging.error("Got and error: {}".format(str(e)))
    return filename

def is_relevant_link_from_html(link):
    """checks that the text content of the link matches the filter_regex
    input parameter is a string
    """
    if filter_regex.match(link):
        return True
    return False
    #return True #Uncomment to grab all links

def dequote(s):
    """Function for deleting paired single or double quotes
    If a string has single or double quotes around it, remove them.
    Make sure the pair of quotes match.
    If a matching pair of quotes is not found, return the string unchanged.
    """
    if (len(s)>= 2 and s[0] == s[-1]) and s.startswith(("'", '"')):
        s = s[1:-1]
    s = s.strip('"\'')
    return s

def extract_text(soup):
    """Extract text from HTML pages and Return normalized text
    https://stackoverflow.com/questions/30565404/remove-all-style-scripts-and-html-tags-from-an-html-page
    return string
    """
    for script in soup(["script", "style"]): # remove all javascript and stylesheet code
        script.extract()
    # get text, the separator keeps the paragraphs their usual short
    # https://stackoverflow.com/a/38861217
    text = soup.get_text(separator="\n")
    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    return '\n'.join(chunk for chunk in chunks if chunk)

def request_url(url, visited_urls):
    """Fuction for requesting url
    Given a URL, go to that url and get the html and return it
    Called from main function
    """
    # Set a header to pretend it's a browser
    headers = requests.utils.default_headers()
    headers.update (
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
        }
    )

    # Log that this URL is being saved
    logging.info('Requesting ' + url)
    visited_urls.write(url)
    visited_urls.write("\n")
    # Use requests module to get html from url as an object
    html = ''
    try:
        r = requests.get(url, headers=headers)
        if r.ok:
            if "text/html" in r.headers["content-type"]:
                return r
        return None
    except requests.exceptions.Timeout:
        # Maybe set up for a retry, or continue in a retry loop
        print("\nTook too long to get the page.")
        logging.info("Took too long to get the page.")
    except requests.exceptions.RequestException as e:
        # catastrophic error. bail.
        print("\nCannot get the page.")
        logging.info("Cannot get the page.")
    except KeyboardInterrupt:
        print("\n\nScript interrupted by user. Shutting down.")
        logging.info("Script interrupted by user")
        shut_down()
    except Exception:
        logging.exception("Couldn\'t request " + url)
        return None

def get_start_page():
    """Open the visited_urls text file and count the number of lines
    in it – that's how many pages the script visited
    throughout its previous runs
    """
    i = 1
    with open("_visited_urls.txt") as f:
        for i, l in enumerate(f, start=1):
            pass
        page = i
    return page

class ChDir(object):
    """
    Step into a directory context on which to operate on.
    """
    def __init__(self, path):
        self.old_dir = os.getcwd()
        self.new_dir = path

    def __enter__(self):
        os.chdir(self.new_dir)

    def __exit__(self, *args):
        os.chdir(self.old_dir)

def get_file_content_as_list(file_name):
    """Give a filename, open and read the contents into a list
    file_name - file to be opened
    return list of words
    """
    with open(file_name, 'r') as file_name_handle:
        return file_name_handle.read().splitlines()

def setup_crawler_files():
    # Open the visited_urls text file
    visited_handler = codecs.open("_visited_urls.txt", "a+", "utf-8")

    # Open the file with planned urls and add them to the array of planned urls
    planned_handler = codecs.open("_planned_urls.txt", "a+", "utf-8")

    # Open the file with crawled urls and add them to the array of crawled urls
    crawled_handler = codecs.open("_crawled_urls.txt", "a+", "utf-8")

    return visited_handler, planned_handler, crawled_handler

def check_domain(new_link, seed):
    """Function that checks if the link provided is in the
    same domain as the seed
    return: boolean
    """
    new_link_domain = tldextract.extract(new_link).domain
    if (new_link_domain == seed):
        return True
    return False

# Shut down gracefully and log it
def shut_down():
    # TODO Close all the things/pipes to files
    sys.exit()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Crawl and scrape a list of URLs for further searching.')

    parser.add_argument(
        '-w',
        '--websites',
        dest='websites',
        default=None,
        required=True,
        help='The file containing list of websites URLs (mandatory)'
    )
    parser.add_argument(
        '-b',
        '--batch',
        dest='batch',
        default=None,
        required=True,
        help='Name for this batch of processing (mandatory)'
    )
    parser.add_argument(
        '-r',
        '--resume',
        dest='resume',
        default=30,
        required=False,
        help="Check if the given batch exists and attempt to resume" \
        " if not complete."
    )
    parser.add_argument(
        '-m',
        '--max_pages',
        dest='max_pages',
        default=10000,
        required=False,
        help="The maximum number of pages to crawl per website"
    )

    # these are module global variables and can be access by any function in
    # this module
    args = parser.parse_args()
    websites_file = args.websites
    batch_name = args.batch
    resume_attempt = args.resume
    max_pages = int(args.max_pages)

    try:
        main()
    except KeyboardInterrupt as e:
        logger.info("Script interrupted by user")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
