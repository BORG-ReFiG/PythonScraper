import requests
from bs4 import BeautifulSoup
import urllib.parse
import os.path
import sys
import tldextract
import time
import codecs
import string
try:
    from os import scandir, walk
except ImportError:
    from scandir import scandir, walk
import logging

#Pay attention to robots.txt

# current time, used in the names of the folder and the logging file
curtime = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())

# Arguments in order: url, total pages to look at, depth, first part of directory name
# url to start from
url = sys.argv[1]
# number of pages to iterate through
iterate = int(sys.argv[2])
# depth to go for
depth_to_go = int(sys.argv[3])
# directory name
directory = sys.argv[4] + "_" + curtime


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

# Check if the directory exists
if not os.path.isdir(directory):
    os.mkdir(directory)  # if it doesnt then make it
os.chdir(directory)  # then change directory to that folder

# Create a log file in the folder that was just created
logging.basicConfig(filename=('_uniscraperlog_' + curtime + '.log'),level=logging.INFO)
# file to log empty requests into
empty_request_log = codecs.open("_empty_requests.txt", "w", "utf-8-sig")
# file to log planned urls into - URLs in the queue, that are planned to go to next (checked against visited)
planned_urls = codecs.open("_planned_urls.txt", "w", "utf-8-sig")
# file to log visited urls into - URLs that have been requested and have the html
visited_urls = codecs.open("_visited_urls.txt", "w", "utf-8-sig")
# file to log crawled urls into - URLs that crawler will "check" against to see if needs logging
crawled_urls = codecs.open("_crawled_urls.txt", "w", "utf-8-sig")


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
    source_code = requests.get(url, headers=headers)  # variable = requests.get(url)
    # Get source code of page as text
    html = source_code.text
    return html


# Function for manually cleaning up name
# Deprecated, we use format_filename instead now
def clean_name (name):
    name = name.replace("\n", "")
    name = name.replace("\r", "")
    name = name.replace("\t", "")
    name = name.replace("|", "")
    name = name.replace(":", "")
    name = name.replace("?", "")
    name = name.replace("'", "")

    # "/"
    # "\\"
    # "*"
    # "\""
    # "<"
    # ">"
    # "^"
    # "!"
    name = name.strip(' ')
    return name


# Function to create a filename out of a string
# Called from create_name
def format_filename(name):
    #Taken from: https://gist.github.com/seanh/93666
    """Take a string and return a valid filename constructed from the string.
    Uses a whitelist approach: any characters not present in valid_chars are
    removed. Also spaces are replaced with underscores.
     
    Note: this method may produce invalid filenames such as ``, `.` or `..`
    When I use this method I prepend a date string like '2009_01_15_19_46_32_'
    and append a file extension like '.txt', so I avoid the potential of using
    an invalid filename."""
    valid_chars = "-_() %s%s" % (string.ascii_letters, string.digits)
    filename = ''.join(c for c in name if c in valid_chars)
    # Remove spaces in filename
    filename = filename.replace(' ','_')
    return filename


# Function for creating name
# Use the title of the html page as the title of the text file
# Called from main function
def create_name (soup):
    try:
        name = soup.title.string  # removes all the unnecessary things from title
        name = format_filename(name)
        logging.info('Created name ' + name)
    except:
        name = "no_title_"  # if no title provided give a no title with number title
        logging.warn('Failed to create a name, using \'' + name + '\' instead')
    return name


# Function for creating file



# Function for saving links


# Main function.
# max_pages is the number of pages to crawl (given as the second argument)
def trade_spider(max_pages):
    logging.info("Crawling through domain '" + seed + "'")
    page = 1

    # Array that holds the queue to be visited later
    plannedURLsArray = [url]
    # Logging the urls
    planned_urls.write(url)
    planned_urls.write("\n")

    # Gets the root of the url
    url_split = url.split("://", 1)
    # Array that holds urls that have been found.
    # This is the array that all new URLs are checked against to prevent repeating.
    # Record URL with both http and https prefixes
    crawledURLsArray = ["http://" + url_split[1]]
    crawledURLsArray.append("https://" + url_split[1])
    # Also log the same into the text file
    crawled_urls.write("http://" + url_split[1] + "\n")
    crawled_urls.write("https://" + url_split[1] + "\n")

    # Sets the depth already crawled to 0
    dsize = 0
    # Create an array of queue size on each level of the tree. Used to stop the crawler at a certain depth.
    # Alas, it appears to be broken...
    depth = [dsize]
    # Checks if the crawler has gone over the max number of pages
    # Also checks if the depth has gone over the max depth
    # Also checks if there are still URLs in the queue
    while page <= max_pages and dsize <= depth_to_go and len(plannedURLsArray) > 0:
        # Empty html variable, just in case
        html = ''
        # Try to get the html of the URL
        try:
            html = request_url(plannedURLsArray[0])
        except:
            logging.warn('Error while requesting an html response ' + plannedURLsArray[0])
        # Checks if html exists and is not empty
        if html:
            # Uses module to parse html into an obejct (a tree of nodes). Nodes are tags, attributes, ect.
            # May need to be re-thought! Very memory heavy. ???
            soup = BeautifulSoup(html, 'html5lib')
            # Gets the name for the file to store the html text in
            name = create_name(soup)
            # Adds the .txt to the end of the name
            name = "{0}.txt".format(name)

            try:
                # Check if file with given name exists
                if os.path.isfile(name):
                    # If exists, add timestamp to name to make it unique.
                    name = name[:name.find(".")] + "_" + str(time.time()) + ".txt"
                
                # Open/create the file with that name
                fo = codecs.open(name, "w", "utf-8-sig")
                # Write URL to that file
                fo.write("<page_url href=\"")
                fo.write(plannedURLsArray[0])
                fo.write("\"></page_url>\n")
                # Append the html to the file
                fo.write(html)
                # Close the pipe to the file
                fo.close()
                # Log the creation of the file
                logging.info('Created file ' + name)

                #print(plannedURLsArray[0])
                # Looks for tables with content (hopefully programs and courses)
                # ACALOG-specific: find all tables with class "block_n2_and_content"
                for table in soup.findAll('table', class_='block_n2_and_content'):
                # Old code: look for all <a> (links) in soup
                #for link in soup.findAll('a', href=True): #Untab the lines below if you uncomment this
                    # Make sure to only collect from the site we want
                    for link in table.findAll('a', href=True):
                        # Collects the href string and stores the link as a tuple
                        # It stores the URL without a #thing and without an ending slash
                        new_link = (urllib.parse.urldefrag(link['href'])[0]).rstrip('/')
                        # ACALOG-specific: removes ACALOG print-friendly format descriptor
                        #new_link = new_link.rstrip('&print')
                        # Smart function for relative links on the page. Joins given path and current URL. 
                        new_link = urllib.parse.urljoin(plannedURLsArray[0], new_link)
                        # Checks if the just found link is in the same domain
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
            except:
                logging.warning("Can not encode file: " + plannedURLsArray[0])
        # Else: html does not exist or is empty. Log error
        else:
            logging.warning('Request for ' + url + ' returned empty html')
            empty_request_log.write(url)
            empty_request_log.write("\n")
        # Prints to console.
        # Update on what URL is being examined
        print(plannedURLsArray[0])
        # Update on the depth it is at
        print("depth:", dsize)
        # Update on the total number of pages
        print("iterations:", page, "pages")
        print("\n")
        # Deletes the currently looked at URL from the queue
        plannedURLsArray.pop(0)
        # SUPER BROKEN???
        # Supposed to check if given depth has been reached
        # Should look at the plannedURLsArray instead of the crawled one
        if page >= depth[dsize]:
            depth.append(len(crawledURLsArray))
            dsize += 1

        # Increment page count
        page += 1
        # Checks the size of the folder. Prints the amount of data collected in GB to the console and log file
        if page%100 == 0:
            size_of_directory = get_tree_size(os.curdir) / 1000000000
            print("Size: ", round(size_of_directory, 5), "GB")
            print('\n')
            logging.info("Size: " + round(size_of_directory, 5) + "GB")
            # Prints in the log file the length of time the crawler has been running in seconds
            logging.info("Has been running for " + str(time.time() - start_time) + " seconds")
        # Time delay in seconds to prevent crashing the server
        time.sleep(.01)

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
trade_spider(iterate)
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