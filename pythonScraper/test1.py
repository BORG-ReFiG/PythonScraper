
from bs4 import BeautifulSoup
import urllib
import urllib.request 


response = urllib.request.urlopen('http://ualberta.ca')
html = response.read()

soup = BeautifulSoup( html, "html.parser")



p = soup.p
a = soup.find_all('a')
urls = []


newurl = 'https://www.ualberta.ca/current-students'
o = urllib.parse.urlparse(newurl)
host = o.hostname

print(o.hostname)
print(o.path)

'''


for link in a:
	url = link.get('href')
	domain = 
		if :
			urls.append(url)


print(urls)

#print (a)


'''