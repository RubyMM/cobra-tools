from generated.formats.ovl.compound.DataEntry import DataEntry
import typing
from generated.formats.ovl.compound.HeaderType import HeaderType
from generated.formats.ovl.compound.HeaderEntry import HeaderEntry
from generated.formats.ovl.compound.Fragment import Fragment
from generated.formats.ovl.compound.SizedStringEntry import SizedStringEntry
from generated.formats.ovl.compound.BufferEntry import BufferEntry


class OvsHeader:

	"""
	Description of one archive's content
	"""
	header_types: typing.List[HeaderType]
	header_entries: typing.List[HeaderEntry]
	data_entries: typing.List[DataEntry]
	buffer_entries: typing.List[BufferEntry]
	sized_str_entries: typing.List[SizedStringEntry]
	fragments: typing.List[Fragment]

	def __init__(self, arg=None, template=None):
		self.arg = arg
		self.template = template
		self.io_size = 0
		self.header_types = []
		self.header_entries = []
		self.data_entries = []
		self.buffer_entries = []
		self.sized_str_entries = []
		self.fragments = []

	def read(self, stream):

		io_start = stream.tell()
		self.header_types = [stream.read_type(HeaderType) for _ in range(self.arg.num_header_types)]
		self.header_entries = [stream.read_type(HeaderEntry) for _ in range(self.arg.num_headers)]
		self.data_entries = [stream.read_type(DataEntry) for _ in range(self.arg.num_datas)]
		self.buffer_entries = [stream.read_type(BufferEntry) for _ in range(self.arg.num_buffers)]
		self.sized_str_entries = [stream.read_type(SizedStringEntry) for _ in range(self.arg.num_files)]
		self.fragments = [stream.read_type(Fragment) for _ in range(self.arg.num_fragments)]

		self.io_size = stream.tell() - io_start

	def write(self, stream):

		io_start = stream.tell()
		for item in self.header_types: stream.write_type(item)
		for item in self.header_entries: stream.write_type(item)
		for item in self.data_entries: stream.write_type(item)
		for item in self.buffer_entries: stream.write_type(item)
		for item in self.sized_str_entries: stream.write_type(item)
		for item in self.fragments: stream.write_type(item)

		self.io_size = stream.tell() - io_start

	def __repr__(self):
		s = 'OvsHeader [Size: '+str(self.io_size)+']'
		s += '\n	* header_types = ' + self.header_types.__repr__()
		s += '\n	* header_entries = ' + self.header_entries.__repr__()
		s += '\n	* data_entries = ' + self.data_entries.__repr__()
		s += '\n	* buffer_entries = ' + self.buffer_entries.__repr__()
		s += '\n	* sized_str_entries = ' + self.sized_str_entries.__repr__()
		s += '\n	* fragments = ' + self.fragments.__repr__()
		s += '\n'
		return s