import requests
from bs4 import BeautifulSoup
import urllib.parse
import os.path
import sys
import tldextract
import time
import codecs
try:
    from os import scandir, walk
except ImportError:
    from scandir import scandir, walk
import logging


#Pay attention to robots.txt

curtime = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime()) #current time, used in the names of the folder and the logging file

url = sys.argv[1]  # url to start from
iterate = int(sys.argv[2]) #number of pages to iterate through
depth_to_go = int(sys.argv[3])  # depth to go for
directory = sys.argv[4] + "_" + curtime # directory name
if not url.startswith("http"):
    url = "http://" + url
seed = tldextract.extract(url).domain


#set a header to pretend it's a browser
headers = requests.utils.default_headers()
headers.update (
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:51.0) Gecko/20100101 Firefox/51.0',
    }
)

if not os.path.isdir(directory):  # check if the directory exists
    os.mkdir(directory)  # if it doesnt then make it
os.chdir(directory)  # then change directory to that folder


logging.basicConfig(filename=('_uniscraperlog_' + curtime + '.log'),level=logging.INFO)


#file to log empty requests into
empty_request_log = codecs.open("_empty_requests.txt", "w", "utf-8-sig")

#file to log planned urls into
planned_urls = codecs.open("_planned_urls.txt", "w", "utf-8-sig")

#file to log visited urls into
visited_urls = codecs.open("_visited_urls.txt", "w", "utf-8-sig")

#file to log planned urls into
crawled_urls = codecs.open("_crawled_urls.txt", "w", "utf-8-sig")



#checks if the link provided is in the same domain as the seed
def checkDomain(link):
    link_domain = tldextract.extract(link)
    return (link_domain.domain == seed)



#fuction for requesting url
def request_url(url):
    global headers
    logging.info('Requesting ' + url)
    visited_urls.write(url)
    visited_urls.write("\n")
    source_code = requests.get(url, headers=headers)  # variable = requests.get(url)
    html = source_code.text  # get source code of page

    return html



#function for cleaning up name
def clean_name (name):
    name = name.replace("\n", "")
    name = name.replace("\r", "")
    name = name.replace("\t", "")
    name = name.replace("|", "")
    name = name.replace(":", "")
    name = name.replace("?", "")
    name = name.replace("'", "")
    name = name.strip(' ')
    return name


#function for creating name
def create_name (soup):
    global title_number
    try:
        name = soup.title.string  # removes all the uncessary things from title
        name = clean_name(name)
        logging.info('Created name ' + name)
    except:
        name = "no_title_" + str(title_number)  # if no title provided give a no title with number title
        title_number += 1
        logging.warn('Failed to create a name, using \'' + name + '\' instead')
    return name




#function for creating file




#function for saving links




# max_pages is the number of pages to crawl
def trade_spider(max_pages):  # function(maximum number of pages to call variable)
    logging.info("Crawling through domain '" + seed + "'")
    page = 1

    urls = [url]
    planned_urls.write(url)
    planned_urls.write("\n")

    url_split = url.split("://", 1)
    visited = ["http://" + url_split[1]]
    visited.append("https://" + url_split[1])
    crawled_urls.write("http://" + url_split[1])
    crawled_urls.write("\n")
    crawled_urls.write("https://" + url_split[1])
    crawled_urls.write("\n")

    title_number = 0  # this is to make sure no two files are named the same way

    dsize = 0  # makes the depth already crawled 0
    depth = [dsize]
    # this checks if pg < max pg, the depth is < depth_to_go, and that urls are still available
    i = 0
    while page <= max_pages and depth_to_go >= dsize and len(urls) > 0:
        #try:
        try:
            html = request_url(urls[0])
        except:
            logging.warn('Error while requesting an html response ' + urls[0])
        if html:
            soup = BeautifulSoup(html, 'html5lib')  # variable to call beautifulsoup(variable of the source code)
            name = create_name(soup)
            name = "{0}.txt".format(name)  # adds the .txt to the end of the name
            try:
                if os.path.isfile(name): 
                    name = name[:name.find(".")] + "_" + str(time.time()) + ".txt" # if the file doesn't exist makes it
                
                fo = codecs.open(name, "w", "utf-8-sig")
                fo.write("<page_url href=\"")
                fo.write(urls[0])
                fo.write("\"></page_url>\n")
                fo.write(html)
                fo.close()

                logging.info('Created file ' + name)

                """
                else:  # if it does exists checks if it's the same file
                    #open original file, read it starting from second line
                    '''with open(name) as double:
                        compare_html = double.readlines()[1:]
                    '''

                    #need a better way to create new name, since there could be more than one double
                    #unfortunate, since i might need to run through all the different copies that could be doubles...
                    #how about for now I just create all the different files even if they are copies of each other
                    new_name = name[:name.find(".")]
                    new_name += "_" + time.time() + ".txt"
                    fo = codecs.open(new_name, "w", "utf-8-sig")
                    fo.write('<page_url href=\"' + urls[0] + '\"></page_url>\n' + html)
                    fo.close()

                    '''

                    size = os.stat(name)
                    size = size.st_size

                    size2 = os.stat(new_name)
                    size2 = size2.st_size
                    #print('made new name ' + new_name)

                    if size == size2:
                        os.remove(new_name)
                    if size2 == 0:
                        os.remove(new_name)
                    '''
                """
                #print(urls[0])
                for table in soup.findAll('table', class_='block_n2_and_content'):
                    for link in table.findAll('a', href=True): #this is new, it makes sure to only collect from the site we want
                    # for ACALOG-based find all tables with class "block_n2_and_content"
                        new_link = (urllib.parse.urldefrag(link['href'])[0]).rstrip('/')
                        new_link = new_link.rstrip('&print')
                        new_link = urllib.parse.urljoin(urls[0], new_link)
                        if checkDomain(new_link):
                            if new_link not in visited:  # if the link is not in visited then it appends it to urls and visited
                                if new_link.startswith("http") and '.pdf' not in new_link and '.jpg' not in new_link: #makes sure no jpg or pdfs pass
                                    #TODO: add checks for www.domain.com and https://
                                    urls.append(new_link)
                                    planned_urls.write(new_link)
                                    planned_urls.write("\n")

                                    http_split = new_link.split("://", 1)
                                    visited.append("http://" + http_split[1])
                                    crawled_urls.write("http://" + http_split[1])
                                    crawled_urls.write("\n")

                                    visited.append("https://" + http_split[1])
                                    crawled_urls.write("https://" + http_split[1])
                                    crawled_urls.write("\n")

            except:
                logging.warning("Can not encode file: " + urls[0])
        else:
            logging.warning('Request for ' + url + ' returned empty html')
            empty_request_log.write(url)
            empty_request_log.write("\n")
        #except:
            #print("Error: Encoding")

        print(urls[0])
        print("depth:", dsize)
        print("iterations:", page, "pages")
        print("\n")
        urls.pop(0)

        if page >= depth[dsize]:
            depth.append(len(visited))
            dsize += 1

        page += 1
        # prints the amount of data collected in GB

        if page%100 == 0:
            size_of_directory = get_tree_size(os.curdir) / 1000000000
            print("Size: ", round(size_of_directory, 5), "GB")
            print('\n')
            logging.info("Size: " + round(size_of_directory, 5) + "GB")
            logging.info("Has been running for " + str(time.time() - start_time) + " seconds")
        time.sleep(.01)



def get_tree_size(path):
    """Return total size of files in given path and subdirs."""
    total = 0
    for entry in scandir(path):
        if entry.is_dir(follow_symlinks=False):
            total += get_tree_size(entry.path)
        else:
            total += entry.stat(follow_symlinks=False).st_size
    return total


start_time = time.time()
trade_spider(iterate)
end_time = time.time()

print("Overall time: " + str((end_time - start_time)))
logging.info("Overall time: " + str((end_time - start_time)))

empty_request_log.close()
visited_urls.close()
planned_urls.close()
crawled_urls.close()
