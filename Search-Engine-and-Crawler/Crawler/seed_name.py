import requests
from bs4 import BeautifulSoup
import urllib.parse
import os.path
import sys

url = sys.argv[1]  # url to start from
iterate = int(sys.argv[2])
depth_to_go = int(sys.argv[3])  # depth to go for
directory = sys.argv[4]  # directory name
if not url.startswith("http"):
    url = "http://" + url