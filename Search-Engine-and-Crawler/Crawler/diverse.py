import requests
import urllib.parse
import os.path
import sys
import tldextract
import time
import codecs
import string
import shutil
import re
import csv
from pprint import pprint
from collections import Counter

try:
    from os import scandir, walk
except ImportError:
    from scandir import scandir, walk
import logging

#Pay attention to robots.txt

# current time, used in the names of the folder and the logging file
curtime = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())

# this file should live in the same directory as the script
keywords_file = "keywords.txt"

# the output file of all observed keyword frequencies
csv_file_name  = "results.csv"

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


# Checks if the url includes http at the front
if not url.startswith("http"):
    url = "http://" + url
# Extracts the top level domain from the URL (eg. ualberta.ca, no slashes)
seed = tldextract.extract(url).domain

# Set a header to pretend it's a browser
headers = requests.utils.default_headers()
headers.update (
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0',
    }
)

#os.mkdir(target_dir)  # make a timestampted folder
# Check if the original directory exists
if os.path.isdir(directory):
    #shutil.copy(directory + "/_planned_urls.txt", target_dir)
    #shutil.copy(directory + "/_empty_requests.txt", target_dir)
    #shutil.copy(directory + "/_visited_urls.txt", target_dir)
    #shutil.copy(directory + "/_crawled_urls.txt", target_dir)
    shutil.copytree(directory, target_dir)
    os.chdir(target_dir)  # then change directory to that folder

    #count number visited
    with open("_visited_urls.txt") as f:
        for i, l in enumerate(f, start=1):
            pass
    page = i

    #create array of planned
    with open("_planned_urls.txt") as f:
        content = f.readlines()
        #remove whitespace characters like `\n` at the end of each line
        planned = content[page-1:]
        plannedURLsArray = [x.strip() for x in planned]

    with open("_crawled_urls.txt") as f:
        content = f.readlines()
        #remove whitespace characters like `\n` at the end of each line
        crawledURLsArray = [x.strip() for x in content]

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
    os.mkdir(target_dir)  # make a timestampted folder
    os.chdir(target_dir)  # then change directory to that folder
    shutil.copyfile(current_dir + "/" + keywords_file, keywords_file)
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


dsize = 0
depth = [dsize]

# Function that checks if the link provided is in the same domain as the seed
def checkDomain(link):
    link_domain = tldextract.extract(link)
    return (link_domain.domain == seed)


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
    try:
        source_code = requests.get(url, headers=headers)  # variable = requests.get(url)
        # Get source code of page as text
        html = source_code.text
    except Timeout as e:
        logging.warn('Connection timed out ' + url)
        html = ''
    except:
        logging.warn('Couldn\'t request ' + url)
        html = ''
    return html


# Function to create a filename out of a string
# Called from create_name
def format_filename(name):
    #Taken from: https://gist.github.com/seanh/93666
    """Take a string and return a valid filename constructed from the string.
    Uses a whitelist approach: any characters not present in valid_chars are
    removed. Also spaces are replaced with underscores."""
    valid_chars = "-_() %s%s" % (string.ascii_letters, string.digits)
    filename = ''.join(c for c in name if c in valid_chars)
    # Remove spaces in filename
    filename = filename.strip()
    filename = filename.replace(' ','_')
    return filename


# Function for creating name
# Use the title of the html page as the title of the text file
# Called from main function
def create_name (html):
    name_list = (html.partition("</title")[0]).split("<title") #grab part of html before </title
    name_part = name_list[-1] #grab part of html after <title
    name = name_part.split(">")[-1]
    if name:
    # removes invalid characters from title
        name = format_filename(name)
        logging.info('Created name ' + name)
    else:
        name = "no_title_" + str(time.time()) # if no title provided give a no title with a timestamp
        logging.warn('Failed to create a name, using \'' + name + '\' instead')
    return name


#Function for deleting paired single or double quotes
def dequote(s):
    """
    If a string has single or double quotes around it, remove them.
    Make sure the pair of quotes match.
    If a matching pair of quotes is not found, return the string unchanged.
    """
    if (len(s)>= 2 and s[0] == s[-1]) and s.startswith(("'", '"')):
        return s[1:-1]
    return s


#Function that takes link, saves the contents to text file call href_split
def test_split(max_pages):
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

    # Create an array of queue size on each level of the tree. Used to stop the crawler at a certain depth.
    # Alas, it appears to be broken...
    while page <= max_pages and dsize <= depth_to_go and len(plannedURLsArray) > 0:
        save_current_link()


def extract_text(full_page):
    """Extract text from HTML pages and Return normalized text
    full_page - HTML source code
    return string
    """

    # toss script and noscript tags
    # (?is) - added to ignore case and allow new lines in text as well as support script tags with attributes.
    # https://stackoverflow.com/questions/964459/how-to-remove-text-between-script-and-script-using-python
    raw_text = re.sub(r'(?is)<script[^>]*>(.*?)</script>', "", full_page)

    # toss iframes
    raw_text = re.sub(r'(?is)<iframe[^>]*>(.*?)</iframe>', "", raw_text)

    # toss styles
    raw_text = re.sub(r'(?is)<style[^>]*>(.*?)</style>', "", raw_text)

    # toss no script tags
    raw_text = re.sub("<noscript>.*?</noscript>", "", raw_text)

    # strip tags and html comments
    raw_text = re.sub(r'(?is)<.*?>',"", raw_text)

    # There were successive space characters to remove after stripping HTML tags out
    raw_text = re.sub(r'\s\s+', ' ', raw_text)

    # Remove html entities
    raw_text = re.sub(r'&nbsp;', ' ', raw_text)
    raw_text = re.sub(r'&copy;', ' ', raw_text)
    raw_text = re.sub(r'&amp;', ' ', raw_text)
    raw_text = re.sub(r'&ldquo;', '“', raw_text)
    raw_text = re.sub(r'&rdquo;', '”', raw_text)
    raw_text = re.sub(r'&rsquo;', '’', raw_text)
    raw_text = re.sub(r'&ndash;', '–', raw_text)
    raw_text = re.sub(r'&mdash;', '—', raw_text)
    raw_text = re.sub(r'&hellip;', '…', raw_text)
    raw_text = re.sub(r'&#39;', "'", raw_text)

    return raw_text.lower()

def tokenize_page(page_text):
    """Create a list of all the words in the page
    page_text - Raw text
    return list of words
    """
    tokenized_words = re.findall(r'[\w]+', page_text)
    return tokenized_words

def get_file_content_as_list(file_name):
    """Give a filename, open and read the contents into a list
    file_name - file to be opened
    return list of words
    """
    with open(file_name, 'r') as file_name_handle:
        return file_name_handle.read().splitlines()

def count_keywords(list_of_tokens, list_of_target_words):
    """Counts how many instances of the keywords were found
    list_of_tokens - The list of words as haystack
    list_of_target_words - The list of words as needle
    return number of words, list of keywords found
    """
    num_target_words = 0
    matched_words = []
    for token in list_of_tokens: # Goes through the tokens in the list
        if token in list_of_target_words: # For each one it checks if it is in the target list
            num_target_words += 1
            matched_words.append(token)
    return num_target_words, matched_words # Note that we are returning a tuple (2 values)

def write_csv(output_file, keywords_header, keywords_x_freqs):
    """Write a CSV file in the format url, <keyword1>, <keyword2>, <keyword3>, ...
    output_file - the name of created CSV file
    keywords_header - list with all the keywords to create header row of CSV
    keywords_x_freqs - dictionary list with keywords and frequencies
    return boolean
    """
    try:
        if os.path.exists(output_file):
            append_write = 'a' # append if already exists
        else:
            append_write = 'w' # make a new file if not

        with open(csv_file_name, append_write) as f:
           # Using dictionary keys as fieldnames for the CSV file header
           writer = csv.DictWriter(f, keywords_header)
           if append_write == 'w':
               writer.writeheader()

           for d in keywords_x_freqs:
              writer.writerow(d)
        return True
    except Exception as e:
        logging.error('Something bad happend while writing CSV:' + str(e))
        return False

def save_current_link ():
    global dsize
    global page

    html = ''
    current_url = plannedURLsArray[0]
    # Try to get the html of the URL
    try:
        html = request_url(current_url)
    except:
        logging.warn('Error while requesting an html response ' + current_url)

    if html:
        plain_text = extract_text(html)
        page_words = tokenize_page(plain_text)

        # read keywords from file into a list
        keywords = get_file_content_as_list(keywords_file)
        # make the keywords lowercase
        keywords = [x.lower() for x in keywords]
        # make keywords dictionary with zero frequency as value
        all_keywords = dict((el,0) for el in keywords)

        # counts keywords in page
        found_count, found_keywords = count_keywords(page_words, keywords)

        found_keywords_freq_dict = Counter(found_keywords)
        all_keywords_dict = Counter(all_keywords)
        # combine both dicts to have uniform dictionary for all pages
        all_keywords_dict.update(found_keywords_freq_dict)
        # after merging, sort the resulting dictionary based on keys to make
        # a tuples list that is always uniform for every page
        sorted_keywords_list = sorted(all_keywords_dict.items())

        # create a sorted dictionary list
        my_d = []
        my_d.append({x:y for x,y in sorted_keywords_list})

        # extract a sorted list of keywords to write as CSV headers
        headers = [str(x) for x, y in sorted_keywords_list]
        # prepend url header onto the keywords list
        headers.insert(0, u'url')
        logging.info(headers)

        # prepend the current URL onto the frequencies dict object
        my_d[0]['url']= current_url

        write_csv(csv_file_name, headers, my_d)

        # Gets the name for the file to store the html text in
        name = create_name(html)

        # Log the creation of keywords
        logging.info('Created keywords for file ' + name)

        #find and process all links
        process_links(html, current_url)

    # Else: html does not exist or is empty. Log error
    else:
        logging.warning('Request for ' + url + ' returned empty html')
        empty_request_log.write(url)
        empty_request_log.write("\n")

    print(plannedURLsArray[0])
    # Update on the depth it is at
    print("depth:", dsize)
    # Update on the total number of pages
    print("iterations:", page, "pages")
    print("\n")
    # Deletes the currently looked at URL from the queue
    plannedURLsArray.pop(0)
    # Check if given depth has been reached
    if page >= depth[dsize]:
        depth.append(page + len(plannedURLsArray))
        dsize += 1

    # Increment page count
    page += 1
    # Checks the size of the folder. Prints the amount of data collected in GB to the console and log file
    if page%10 == 0:
        size_of_directory = get_tree_size(os.curdir) / 1000000000
        print("Size: ", str(round(size_of_directory, 5)), "GB")
        print('\n')
        logging.info("Size: " + str(round(size_of_directory, 5)) + "GB")
        # Prints in the log file the length of time the crawler has been running in seconds
        logging.info("Has been running for " + str(time.time() - start_time) + " seconds")
    # Time delay in seconds to prevent crashing the server
    time.sleep(.01)


#Function for splitting html into links
def href_split (html):
    links = []
    if html.partition('<body')[2]:
        html = html.partition('<body')[2]
    link_strings = html.split('href=')
    for lnk in link_strings[1:]:
        href = lnk.partition('>')[0]
        href = href.partition(' ')[0]
        href = dequote(href)
        links.append(href)
    return links


#Take an array of links, run the split on each and add the results to the appropriate arrays and files
def process_links(html, cur_domain):
    if html.partition('<body')[2]:
        html = html.partition('<body')[2]
    link_strings = html.split('href=')
    for lnk in link_strings[1:]:
        href = lnk.partition('>')[0]
        href = href.partition(' ')[0]
        href = dequote(href)
        new_link = (urllib.parse.urldefrag(href)[0]).rstrip('/')
        new_link = urllib.parse.urljoin(cur_domain, new_link)
        if checkDomain(new_link):
            # if the link is not in crawledURLsArray then it appends it to urls and crawledURLsArray
            if new_link not in crawledURLsArray:
                # Ensures no jpg or pdfs are stored and that no mailto: links are stored.
                if new_link.startswith("http") and '.pdf' not in new_link and '.jpg' not in new_link:
                    #???TODO: add checks for www.domain.com and https://
                    # Adds new link to array
                    plannedURLsArray.append(new_link)
                    # Adds new link to queue file
                    planned_urls.write(new_link)
                    planned_urls.write("\n")

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

# Get the time that the command was run
start_time = time.time()
# Call main function
"""trade_spider(iterate)"""
test_split(iterate)
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
