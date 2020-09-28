class DirEntry:

# Description of one directory in the archive

	# offset in the header's Names block
	offset: int

	def __init__(self, arg=None, template=None):
		self.arg = arg
		self.template = template
		self.offset = 0

	def read(self, stream):
		self.offset = stream.read_uint()

	def write(self, stream):
		stream.write_uint(self.offset)

	def __repr__(self):
		s = 'DirEntry'
		s += '\n	* offset = ' + self.offset.__repr__()
		s += '\n'
		return s