from bs4 import BeautifulSoup
import urllib
import urllib.request 
import time
import csv
import library

#url = 'https://www.google.ca/search?q='
url = 'https://www.ualberta.ca/interdisciplinary-studies'

page = urllib.request.urlopen(url)
pagehtml = page.read()

response = urllib.request.urlopen(url)
html = response.read()
newsoup = BeautifulSoup(pagehtml, "html.parser")
soup = BeautifulSoup( html, "html.parser")

body = soup.body
