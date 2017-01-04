

from bs4 import BeautifulSoup
import urllib
import urllib.request 
import time
import csv

keywords = ['video games', '3D animation', 'new media', 'digital media']

homepage = 'https://www.ualberta.ca/faculties-and-programs'

response = urllib.request.urlopen(homepage)
html = response.read()

soup = BeautifulSoup( html, "html.parser")
urls = []

for link in soup.find_all('a'):
	urls.append(link.get('href'))

o = urllib.parse.urlparse(homepage)
host = o.hostname
cleanurl = []

for url in urls:
	x = urllib.parse.urlparse(url)
	site = x.hostname
	if site == host:
		cleanurl.append(url)

with open('ualbertastuff4.csv', 'w', newline='') as csvfile:
	spamwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

	for url in cleanurl:
		print(url)
		spamwriter.writerow([url])
		


'''


	#time.sleep(1)


o = urllib.parse.urlparse(homepage)
host = o.hostname
cleanurl = set()

for url in urls:
	x = urllib.parse.urlparse(url)
	site = x.hostname
	if site == host:
		cleanurl.add(url)

#print(cleanurl)
#for page in cleanurl:
	#get it to look for our keywords




def getUrls(url, homepage):
	page = urllib.request.urlopen(url)
	pagehtml = page.read()
	newsoup = BeautifulSoup(pagehtml, "html.parser")
	soup = BeautifulSoup( html, "html.parser")
	urls = []
	
	for link in soup.find_all('a'):
		urls.append(link.get('href'))
	
	o = urllib.parse.urlparse(homepage)
	host = o.hostname
	url_home = []

	for url in urls:
		x = urllib.parse.urlparse(url)
		site = x.hostname
		if site == host:
			url_home.append(url)
	return url_home


visited = []

for url_clean in cleanurl:
	if not url_clean in visited:
		newUrls = getUrls(url_clean, homepage)
		print("getting urls from another url")
		for x in newUrls:
			cleanurl.add(x)
'''