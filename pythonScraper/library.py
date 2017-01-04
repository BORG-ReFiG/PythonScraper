from bs4 import BeautifulSoup
import urllib
import urllib.request 
import time
import csv

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