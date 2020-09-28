from generated.formats.bnk.compound.HircPointer import HircPointer
import typing


class HIRCSection:

# The HIRC section contains all the Wwise objects, including the events, the containers to group sounds, and the references to the sound files.

	# length of following data
	length: int
	count: int
	hirc_pointers: typing.List[HircPointer]

	def __init__(self, arg=None, template=None):
		self.arg = arg
		self.template = template
		self.length = 0
		self.count = 0
		self.hirc_pointers = HircPointer()

	def read(self, stream):
		self.length = stream.read_uint()
		self.count = stream.read_uint()
		self.hirc_pointers = [stream.read_type(HircPointer) for _ in range(self.count)]

	def write(self, stream):
		stream.write_uint(self.length)
		stream.write_uint(self.count)
		for item in self.hirc_pointers: stream.write_type(item)

	def __repr__(self):
		s = 'HIRCSection'
		s += '\n	* length = ' + self.length.__repr__()
		s += '\n	* count = ' + self.count.__repr__()
		s += '\n	* hirc_pointers = ' + self.hirc_pointers.__repr__()
		s += '\n'
		return s