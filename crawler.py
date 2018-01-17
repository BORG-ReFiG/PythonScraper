#!/usr/bin/env python
import requests
from bs4 import BeautifulSoup
import urllib.parse
import os
import sys
import tldextract
import time
import codecs
import string
import shutil
import re
import uuid

try:
    from os import scandir, walk
except ImportError:
    from scandir import scandir, walk
import logging

#Pay attention to robots.txt

# current time, used in the names of the folder and the logging file
curtime = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())

# this file should live in the same directory as the script
keywords_file = "keywords_game.txt"

# this should be a file input later but for now it's an array
# an array of popular domains that university websites link to but we don't want to crawl
ignore_domains = ["youtube", "facebook", "instagram", "twitter", "linkedin", "google", "pinterest", "snapchat"]

# Arguments in order: url, total pages to look at, depth, first part of directory name
# url to start from
url = sys.argv[1]
# number of pages to iterate through
iterate = int(sys.argv[2])
# depth to go for
depth_to_go = int(sys.argv[3])
# directory name
directory = sys.argv[4]
target_dir = directory + "_" + curtime

# RegEx that is used to filter searches for URLs on any given page.
# Used in is_relevant_link_from_soup and is_relevant_link_from_html functions
filter_regex = re.compile(".*([Pp]rogram|[Aa]dmission|[Cc]ertificate|[Dd]egree|[Dd]iploma|[Ff]aculty|[Ss]chool|[Dd]epartment|[Uu]ndergrad|[Gr]rad).*")
filter_title_regex = re.compile(".*([Pp]rogram|[Aa]dmission|[Cc]ourse).*")

# Var to choose mode
# "soup" uses BeautifulSoup to assign a name to a page and to search the page for URLs
# "no_soup" uses a string search – splits the page into strings using "href=" as a partition limiter, then goes from there
mode = "soup" # soup or no_soup


# Checks if the url includes http at the front
if not url.startswith("http"):
    url = "http://" + url
# Extracts the top level domain from the URL (eg. ualberta.ca, no slashes)
seed = tldextract.extract(url).domain

# Set a header to pretend it's a browser
headers = requests.utils.default_headers()
headers.update (
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
    }
)

# Checks if the directory with the given name already exists
# If it does, tries to continue a script run that was interrupted, using already existing lists of visited_urls and planned_urls
# If it doesn't, starts a new script run
if os.path.isdir(directory):
    # Continuing a previous script run

    # Copy the contents of the existing directory to a new timestamped one
    shutil.copytree(directory, target_dir)
    os.chdir(target_dir)  # then change directory to that folder

    # Open the visited_urls text file and count the number of lines in it – that's how many pages the script visited throughout its previous runs
    with open("_visited_urls.txt") as f:
        for i, l in enumerate(f, start=1):
            pass
    page = i

    # Open the file with planned urls and add them to the array of planned urls
    with open("_planned_urls.txt") as f:
        content = f.readlines()
        #remove whitespace characters like `\n` at the end of each line
        planned = content[page-1:]
        plannedURLsArray = [x.strip() for x in planned]

    # Open the file with crawled urls and add them to the array of crawled urls
    with open("_crawled_urls.txt") as f:
        content = f.readlines()
        #remove whitespace characters like `\n` at the end of each line
        crawledURLsArray = [x.strip() for x in content]

    # Create a new log file
    logging.basicConfig(filename=('_uniscraperlog_' + curtime + '.log'),level=logging.INFO)
    # file to log empty requests into
    empty_request_log = codecs.open("_empty_requests.txt", "a", "utf-8-sig")
    # file to log planned urls into - URLs in the queue, that are planned to go to next (checked against visited)
    planned_urls = codecs.open("_planned_urls.txt", "a", "utf-8-sig")
    # file to log visited urls into - URLs that have been requested and have the html
    visited_urls = codecs.open("_visited_urls.txt", "a", "utf-8-sig")
    # file to log crawled urls into - URLs that crawler will "check" against to see if needs logging
    crawled_urls = codecs.open("_crawled_urls.txt", "a", "utf-8-sig")


else:
    current_dir = os.getcwd()
    # Start a new script run
    os.mkdir(target_dir)  # make a timestampted folder
    os.chdir(target_dir)  # then change directory to that folder
    shutil.copyfile(current_dir + "/" + keywords_file, keywords_file) # jump into working directory
    # Create a log file in the folder that was just created
    logging.basicConfig(filename=('_uniscraperlog_' + curtime + '.log'),level=logging.INFO)
    # file to log empty requests into
    empty_request_log = codecs.open("_empty_requests.txt", "w", "utf-8-sig")
    # file to log planned urls into - URLs in the queue, that are planned to go to next (checked against visited)
    planned_urls = codecs.open("_planned_urls.txt", "w", "utf-8-sig")
    plannedURLsArray = []
    # file to log visited urls into - URLs that have been requested and have the html
    visited_urls = codecs.open("_visited_urls.txt", "w", "utf-8-sig")
    # file to log crawled urls into - URLs that crawler will "check" against to see if needs logging
    crawled_urls = codecs.open("_crawled_urls.txt", "w", "utf-8-sig")
    crawledURLsArray = []
    page = 1

# Function that checks if the link provided is in the same domain as the seed
def checkDomain(new_link, cur_link):
    new_link_domain = tldextract.extract(new_link).domain

    """Decided to not do the can-go-one-domain-away-from-the-seed rule for now. Commented it out.
    # 0) check whether new_link is in the list of popular domains that we don't want to crawl, if yes -> IGNORE IT
    if new_link_domain in ignore_domains:
        return False
    """
    # 1) check if new_link is in seed, if yes -> OK
    if (new_link_domain == seed):
        return True

    """
    # 2) check if cur_link is in seed (you came from the seed even if you're in a different domain now), if yes -> OK
    cur_link_domain = tldextract.extract(cur_link).domain
    if (cur_link_domain == seed):
        return True
    # 3) check if the new link is in the same domain as the cur link (you're still in the same domain, even though it's different from seed), if yes -> OK
    if (new_link_domain == cur_link_domain):
        return True
    # otherwise, you're trying to leave a domain that's already not the seed, you should STOP
    """
    return False


# Fuction for requesting url
# Given a URL, go to that url and get the html and return it
# Called from main function
def request_url(url):
    global headers
    # Log that this URL is being saved
    logging.info('Requesting ' + url)
    visited_urls.write(url)
    visited_urls.write("\n")
    # Use requests module to get html from url as an object
    html = ''
    try:
        head = requests.head(url, headers=headers)
        if head.ok and ("text/html" in head.headers["content-type"]):
            r = requests.get(url, headers=headers)
            if r.ok:
                return r
        return None
    except KeyboardInterrupt:
        print("\n\nScript interrupted by user. Shutting down.")
        logging.info("Script interrupted by user")
        shut_down()
    except Exception:
        logging.exception("Couldn\'t request " + url)
        return None

# Function to create a filename out of a string
# Called from create_name
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


# Function for creating name
# Use the title of the html page as the title of the text file
# Called from process_current_link
# Uses string search to locate the <title> tag
# Parameter html is a string
def create_name_from_html (html):
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

# Function for creating name
# Use the title of the html page as the title of the text file
# Called from process_current_link
# Uses Beautiful Soup to locate the <title> tag
# Parameter soup is a soup object
def create_name_from_soup (soup):
    try:
        name = soup.title.string
        # removes invalid characters from title
        name = format_filename(name) + '__' + str(time.time())
        logging.info('Created name ' + name)
    except AttributeError as e:
        name = "no_title_" + str(time.time()) # if no title provided give a no title with a timestamp
        logging.warn('Failed to create a name, using \'' + name + '\' instead')
        logging.error(str(e))
    return name


#Function for deleting paired single or double quotes
def dequote(s):
    """
    If a string has single or double quotes around it, remove them.
    Make sure the pair of quotes match.
    If a matching pair of quotes is not found, return the string unchanged.
    """
    if (len(s)>= 2 and s[0] == s[-1]) and s.startswith(("'", '"')):
        s = s[1:-1]
    s = s.strip('"\'')
    return s


# Function that takes link, saves the contents to text file call href_split
# Main function
def crawl(max_pages):
    logging.info("Crawling through domain '" + seed + "'")

    if page == 1:
        # Array that holds the queue to be visited later
        plannedURLsArray.append(url)
        # Logging the urls
        planned_urls.write(url)
        planned_urls.write("\n")

        # Gets the root of the url
        url_split = url.split("://", 1)
        # Array that holds urls that have been found.
        # This is the array that all new URLs are checked against to prevent repeating.
        # Record URL with both http and https prefixes
        crawledURLsArray.append("http://" + url_split[1])
        crawledURLsArray.append("https://" + url_split[1])
        # Also log the same into the text file
        crawled_urls.write("http://" + url_split[1] + "\n")
        crawled_urls.write("https://" + url_split[1] + "\n")

    while page <= max_pages and len(plannedURLsArray) > 0:
        process_current_link()


def is_title_page_relevant(soup):
    return True if soup.find('title', string=filter_title_regex) else False

# Function that grabs the first link in the list of planned urls, requests the page and processes it
def process_current_link ():
    global page

    print(plannedURLsArray[0])
    # Try to get the html of the URL
    r = request_url(plannedURLsArray[0])

    if r: #if the request returned an html
        html = r.text
        current_url = r.url
        # Soupify
        # For now it soupifies the link regardless of the mode, because it uses soup later to extract visible text from the page
        soup = BeautifulSoup(html, 'html.parser')
        grab_all = is_title_page_relevant(soup)

        if mode=="no_soup":
            # Gets the name for the file to store the html text in
            name = create_name_from_html(html)
            #find and process all links
            process_links_from_html(html, current_url, grab_all)
        else:
            name = create_name_from_soup(soup)
            process_links_from_soup(soup, current_url, grab_all)

        # Adds the .txt to the end of the name
        name = "{0}.txt".format(name)

        # Find only visible text
        visible_text = extract_text(soup)

        if visible_text: #save it as a text file
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
                print("\n\nScript interrupted by user. Shutting down.")
                logging.info("Script interrupted by user")
                shut_down()
            except Exception:
                logging.exception("Can not encode file: " + current_url)
        else:
            print('No visible text in ' + url)
            logging.warning('No visible text in ' + url)
    # Else: html does not exist or is empty. Log error
    else:
        logging.warning('Request for ' + url + ' returned empty html')
        empty_request_log.write(url)
        empty_request_log.write("\n")

    # Update on the total number of pages
    print("iterations:", page, "pages")
    print("\n")
    # Deletes the currently looked at URL from the queue
    plannedURLsArray.pop(0)

    # Increment page count
    page += 1
    # Every 50 pages checks the size of the folder. Prints the amount of data collected in MB to the console and log file
    if page%50 == 0:
        size_of_directory = get_tree_size(os.curdir) / 1000000
        print("Size: ", str(round(size_of_directory, 5)), "MB")
        print('\n')
        logging.info("Size: " + str(round(size_of_directory, 5)) + "MB")
        # Prints in the log file the length of time the crawler has been running in seconds
        logging.info("Has been running for " + str(time.time() - start_time) + " seconds")
    # Time delay in seconds to prevent crashing the server
    time.sleep(.01)


# checks that the text content of the link matches the filter_regex
# input parameter is a soup element!!!
def is_relevant_link_from_soup(link):
    if link.find(string=filter_regex):
        return True
    return False
    #return True #Uncomment to grab all links

# takes soup of a page, finds all links on it
# for each link checks if it's relevant
# for each relevant link, saves it to the planned urls array (if it hasn't been crawled yet)
# and to the crawled urls array (so that we don't save it a second time later)
def process_links_from_soup (soup, cur_link, grab_all=False):
    # check if the title of the current page matches the filter_title_regex
    for lnk in soup.findAll('a', href=True):
        # if not, check if the the link itself is relevant
        if (grab_all or is_relevant_link_from_soup(lnk)):
            new_link = (urllib.parse.urldefrag(lnk['href'])[0]).rstrip('/')
            new_link = urllib.parse.urljoin(cur_link, new_link)
            # if the link is in our main domain
            if checkDomain(new_link, cur_link):
                # if the link is not in crawledURLsArray then it appends it to urls and crawledURLsArray
                if new_link not in crawledURLsArray:
                    # Ensures no jpg or pdfs are stored and that no mailto: links are stored.
                    if new_link.startswith("http") and ('.pdf' not in new_link) and ('.jpg' not in new_link) and ('.mp3' not in new_link):
                        #???TODO: add checks for www.domain.com and https://
                        # Adds new link to array
                        plannedURLsArray.append(new_link)
                        # Adds new link to queue file
                        planned_urls.write(new_link)
                        planned_urls.write("\n")

                        # Remove the front of the URL (http or https)
                        http_split = new_link.split("://", 1)

                        if len(http_split)>1:
                            # Add all possible link variations to file of URLs that have been looked at
                            # Adds new link to array
                            crawledURLsArray.append("http://" + http_split[1])
                            # Adds new link to already looked at file
                            crawled_urls.write("http://" + http_split[1])
                            crawled_urls.write("\n")
                            # Adds new link to array
                            crawledURLsArray.append("https://" + http_split[1])
                            # Adds new link to already looked at file
                            crawled_urls.write("https://" + http_split[1])
                            crawled_urls.write("\n")

# checks that the text content of the link matches the filter_regex
# input parameter is a string
def is_relevant_link_from_html(link):
    if filter_regex.match(link):
        return True
    return False
    #return True #Uncomment to grab all links

#Take an array of links, run the split on each and add the results to the appropriate arrays and files
def process_links_from_html (html, cur_link, grab_all=False):
    print("grabbing all: ", str(grab_all))
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
            if checkDomain(new_link, cur_link):
                # if the link is not in crawledURLsArray then it appends it to urls and crawledURLsArray
                if new_link not in crawledURLsArray:
                    # Ensures no jpg or pdfs are stored and that no mailto: links are stored.
                    if new_link.startswith("http") and '.pdf' not in new_link and '.jpg' not in new_link and '.mp3' not in new_link:
                        #???TODO: add checks for www.domain.com and https://
                        # Adds new link to array
                        plannedURLsArray.append(new_link)
                        # Adds new link to queue file
                        planned_urls.write(new_link)
                        planned_urls.write("\n")

                        try:
                            # Remove the front of the URL (http or https)
                            http_split = new_link.split("://", 1)
                            # Add all possible link variations to file of URLs that have been looked at
                            # Adds new link to array
                            crawledURLsArray.append("http://" + http_split[1])
                            # Adds new link to already looked at file
                            crawled_urls.write("http://" + http_split[1])
                            crawled_urls.write("\n")
                            # Adds new link to array
                            crawledURLsArray.append("https://" + http_split[1])
                            # Adds new link to already looked at file
                            crawled_urls.write("https://" + http_split[1])
                            crawled_urls.write("\n")
                        except IndexError as e:
                            logging.info(str(e))


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



# Function to extract text elements from an HTML and return them as an array of BeautifulSoup
# called from process_current_link
def _extract_text(soup):
    data = soup.findAll(text=True)
    result = filter(is_visible_html_element, data)
    all_text = ""
    for t in result:
        if t.strip():
            all_text += t + "\n"
    return all_text


# check that the given soup element is a visible text element
# called from extract_text
def is_visible_html_element(element):
    if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
        return False
    elif re.match('<!--.*-->', str(element.encode('utf-8'))):
        return False
    return True






# Return total size of files in given path and subdirs by going through the tree.
# Recursive.
# Called from main function
def get_tree_size(path):
    total = 0
    for entry in scandir(path):
        if entry.is_dir(follow_symlinks=False):
            total += get_tree_size(entry.path)
        else:
            total += entry.stat(follow_symlinks=False).st_size
    return total


# Shut down gracefully and log it
def shut_down():
    global start_time
    global logging
    global empty_request_log
    global visited_urls
    global planned_urls
    global crawled_urls

    # Get the time that the command finished
    end_time = time.time()
    # Print overall time taken to console
    print("Overall time: " + str((end_time - start_time)))
    # Log overall time and save to main log file
    logging.info("Overall time: " + str((end_time - start_time)))
    # Close all the things/pipes to files
    empty_request_log.close()
    visited_urls.close()
    planned_urls.close()
    crawled_urls.close()

    sys.exit()


# Get the time that the command was run
start_time = time.time()

try:
    # Call main function
    crawl(iterate)
    shut_down()
except KeyboardInterrupt:
    print("\n\nScript interrupted by user. Shutting down.")
    logging.info("Script interrupted by user")
    shut_down()
except Exception:
    logging.exception("Error while running script")
