from generated.formats.bnk.compound.BKHDSection import BKHDSection
from generated.formats.bnk.compound.DIDXSection import DIDXSection
# from generated.formats.bnk.compound.DATASection import DATASection
import os
import struct

class AuxFileContainer:
	# Custom file struct

	def __init__(self, arg=None, template=None):
		self.arg = arg
		self.template = template
		self.chunks = []
		self.bhkd = None
		self.didx = None
		self.data = None

	def read(self, stream):
		self.chunks = []
		chunk_id = "DUMM"
		while len(chunk_id) == 4:
			chunk_id = stream.read(4)
			print("reading chunk", chunk_id)
			if chunk_id == b"BKHD":
				self.bhkd = stream.read_type(BKHDSection)
				self.chunks.append((chunk_id, self.bhkd))
			elif chunk_id == b"DIDX":
				self.didx = stream.read_type(DIDXSection)
				self.chunks.append((chunk_id, self.didx))
			elif chunk_id == b"DATA":
				size = stream.read_uint()
				self.data = stream.read(size)
			elif chunk_id == b'\x00\x00\x00\x00':
				break
			elif not chunk_id:
				break
			else:
				raise NotImplementedError(f"Unknown chunk {chunk_id}!")
		for pointer in self.didx.data_pointers:
			pointer.data = self.data[pointer.data_section_offset: pointer.data_section_offset+pointer.wem_filesize]
			pointer.hash = "".join([f"{b:02X}" for b in struct.pack("<I", pointer.wem_id)])

	def extract_audio(self, out_dir, basename):
		"""Extracts all wem files from the container into a folder"""
		print("Extracting audio")
		paths = []
		for pointer in self.didx.data_pointers:
			wem_name = f"{basename}_{pointer.hash}.wem"
			wem_path = os.path.normpath(os.path.join(out_dir, wem_name))
			paths.append(wem_path)
			print(wem_path)
			with open(wem_path, "wb") as f:
				f.write(pointer.data)
		return paths

	def inject_audio(self, wem_path, wem_id):
		"""Loads wem audio into the container"""
		print("Injecting audio")
		for pointer in self.didx.data_pointers:
			if pointer.hash == wem_id:
				print("found a match, reading wem data")
				with open(wem_path, "rb") as f:
					pointer.data = f.read()
				break

	def write(self, stream):
		"""Update representation, then write the container from the internal representation"""
		offset = 0
		for pointer in self.didx.data_pointers:
			pointer.data_section_offset = offset
			pointer.wem_filesize = len(pointer.data)
			offset += len(pointer.data)
			# todo - do padding here, might speed up loading?
		for chunk_id, chunk in self.chunks:
			stream.write(chunk_id)
			stream.write_type(chunk)
		data = b"".join(pointer.data for pointer in self.didx.data_pointers)
		stream.write(b"DATA")
		stream.write_uint(len(data))
		stream.write(data)

	def __repr__(self):
		s = 'AuxFileContainer'
		for chunk in self.chunks:
			s += '\nchunk ' + chunk.__repr__()
		s += '\n'
		return s