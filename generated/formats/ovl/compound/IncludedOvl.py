from generated.context import ContextReference


class IncludedOvl:

	"""
	Description of one included ovl file that is force-loaded by this ovl
	"""

	context = ContextReference()

	def __init__(self, context, arg=None, template=None):
		self.name = ''
		self._context = context
		self.arg = arg
		self.template = template
		self.io_size = 0
		self.io_start = 0

		# offset in the header's names block. path is relative to this ovl's directory, without the .ovl suffix
		self.offset = 0
		self.set_defaults()

	def set_defaults(self):
		self.offset = 0

	def read(self, stream):
		self.io_start = stream.tell()
		self.offset = stream.read_uint()

		self.io_size = stream.tell() - self.io_start

	def write(self, stream):
		self.io_start = stream.tell()
		stream.write_uint(self.offset)

		self.io_size = stream.tell() - self.io_start

	def get_info_str(self):
		return f'IncludedOvl [Size: {self.io_size}, Address: {self.io_start}] {self.name}'

	def get_fields_str(self):
		s = ''
		s += f'\n	* offset = {self.offset.__repr__()}'
		return s

	def __repr__(self):
		s = self.get_info_str()
		s += self.get_fields_str()
		s += '\n'
		return s
