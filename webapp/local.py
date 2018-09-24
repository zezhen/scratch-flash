
import os

class Local(object):
	def __init__(self, logger):
		self.logger = logger

	def upload_convert_get_link(self, _user, _filename, _byte):
		pass

	def upload_local_file(self, src, dest):
		pass

	def get_url(self, path, is_public=False):
		return path

	def get_cdn_url(self):
		return ''

	def is_object_exist(self, path):
		return os.path.isfile(path)