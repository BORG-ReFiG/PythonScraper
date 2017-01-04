from bs4 import BeautifulSoup
import urllib
import urllib.request 
import time
import csv
import library


def getUrls(url, homepage):
	page = urllib.request.urlopen(url)
	pagehtml = page.read()
	newsoup = BeautifulSoup(pagehtml, "html.parser")
	soup = BeautifulSoup( html, "html.parser")
	urls = []
	
	for link in soup.find_all('a'):
		urls.append(link.get('href'))
	
	o = urllib.parse.urlparse(homepage)
	host = o.netloc
	url_home = []

	for url in urls:
		x = urllib.parse.urlparse(url)
		site = x.netloc
		if site == host:
			url_home.append(url)
	return url_home



keywords = ['video games', '3D animation', 'new media', 'digital media']

homepage = 'https://www.ualberta.ca/'

response = urllib.request.urlopen(homepage)
html = response.read()

soup = BeautifulSoup( html, "html.parser")
urls = []

for link in soup.find_all('a'):
	urls.append(link.get('href'))
	#time.sleep(1)


o = urllib.parse.urlparse(homepage)
host = o.netloc
cleanurl = []

visited = []

for url in urls:
	x = urllib.parse.urlparse(url)
	site = x.netloc
	if site == host:
		cleanurl.append(url)

with open('ualbertastuff7.csv', 'w', newline='') as csvfile:
	spamwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)


	while len(cleanurl) > 0:
		urlz = cleanurl.pop(0)
		if not urlz in visited:
			time.sleep(.01)
			visited.append(urlz)
			print(urlz)
			spamwriter.writerow([urlz])
			newUrls = getUrls(urlz, homepage)
			for sites in newUrls:
				cleanurl.append(sites)





#print(cleanurl)
#for page in cleanurl:
	#get it to look for our keywords





'''



with open('ualbertastuff2.csv', 'w', newline='') as csvfile:
	spamwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

	for url_clean in cleanurl:
		if not url_clean in visited:
			time.sleep(.01)
			newUrls = getUrls(url_clean, homepage)
			print(url_clean)
			visited.append(url_clean)
			spamwriter.writerow([url_clean])
			for x in newUrls:
				cleanurl.append(x)








p = soup.p



print(a)

'''
