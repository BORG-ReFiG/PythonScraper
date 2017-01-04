



class UrlClean:
	"""docstring for UrlClean"""
	
	def __init__(self, url, date):
		super(UrlClean, self).__init__()
		
		self.visited = False
		self.url = url
		self.date = date


	def set_keywords(self, keywords):

		self.keywords = keywords

