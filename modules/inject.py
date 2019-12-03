import struct
import os
import io
from pyffi.formats.dds import DdsFormat
from pyffi.formats.ms2 import Ms2Format
from pyffi.formats.bani import BaniFormat
from pyffi.formats.ovl import OvlFormat

from modules import extract
from util import texconv

def inject(ovl_data, file_paths):
	for file_path in file_paths:
		dir, name_ext = os.path.split(file_path)
		print("Injecting",name_ext)
		name, ext = os.path.splitext(name_ext)
		ext = ext.lower()
		if ext in (".dds", ".png"):
			name_ext = name+".tex"
		# find the sizedstr entry that refers to this file
		sized_str_entry = ovl_data.get_sized_str_entry(name_ext)
		if ext == ".mdl2":
			load_mdl2(ovl_data, file_path, sized_str_entry)
		elif ext == ".png":
			load_png(ovl_data, file_path, sized_str_entry)
		elif ext == ".dds":
			load_dds(ovl_data, file_path, sized_str_entry)
		elif ext == ".txt":
			load_txt(ovl_data, file_path, sized_str_entry)

def load_txt(ovl_data, txt_file_path, txt_sized_str_entry):
	# currently just overwriting, which is dangerous
	padding = bytes.fromhex("00 00 00 00")
	
	archive = ovl_data.archives[0]
	# first ensure each sized str entry has the current
	print("storing current data")
	for sized_str_entry in archive.sized_str_entries:
		# read header data and store it in sized_str_entry object
		sized_str_entry.data = archive.get_header_data(sized_str_entry)
		print(sized_str_entry.data)
	
	print("injecting current data")
	with open(txt_file_path, 'rb') as stream:
		raw_txt_bytes = stream.read()
		txt_sized_str_entry.data = struct.pack("<I", len(raw_txt_bytes)) + raw_txt_bytes + padding
		txt_sized_str_entry.pointers[0].data_size = len(txt_sized_str_entry.data)
		# print(txt_sized_str_entry.data)
	
	# clear io objects
	archive.headers_data_io = list( io.BytesIO() for h in archive.header_entries )
	
	# write updated strings
	for sized_str_entry in archive.sized_str_entries:
		# get header_data to write into
		writer = archive.headers_data_io[txt_sized_str_entry.pointers[0].header_index]
		# update data offset
		sized_str_entry.pointers[0].data_offset = writer.tell()
		# write data to io, adjusting the cursor for that header
		writer.write(sized_str_entry.data)
	
def load_png(ovl_data, png_file_path, tex_sized_str_entry):
	# convert the png into a dds, then inject that
	
	archive = ovl_data.archives[0]
	header_3_0, header_3_1, header_7 = extract.get_tex_structs(archive, tex_sized_str_entry)
	dds_compression_type = extract.get_compression_type(archive, header_3_0)
	compression = dds_compression_type.replace("DXGI_FORMAT_","")
	# print(compression)
	# print(header_7.num_mips)
	dds_file_path = texconv.save_dds_texconv( png_file_path, codec = compression, mips = header_7.num_mips)
	load_dds(ovl_data, dds_file_path, tex_sized_str_entry)
	# os.remove(dds_file_path)

def pack_mips_for_jwe(stream, header):
	# eoh = stream.tell()
	normal_levels = []
	packed_levels = []
	
	# get compression type
	dds_types = {}
	dds_enum = DdsFormat.DxgiFormat
	for k, v in zip(dds_enum._enumkeys, dds_enum._enumvalues):
		dds_types[v] = k
	comp = dds_types[header.dx_10.dxgi_format]
	
	# get bpp from compression type
	if "BC1" in comp or "BC4" in comp:
		pixels_per_byte = 2
		empty_block = bytes.fromhex("00 00 00 00 00 00 00 00")
	else:
		pixels_per_byte = 1
		empty_block = bytes.fromhex("00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00")
	
	
	h = header.height
	w = header.width
	mip_i = 0
	
	
	print("\nstandard mips")
	# the last normal mip is 64x64
	# no, wrong, check herrera pbasecolor
	# start packing when one line of the mip == 128 bytes
	while w // pixels_per_byte > 32:
		print(mip_i, h, w)
		num_pixels = h * w * header.dx_10.array_size
		num_bytes = num_pixels // pixels_per_byte
		address = stream.tell()
		print(address, num_pixels, num_bytes)
		normal_levels.append( (h, w, stream.read(num_bytes)) )
		# dds_buff = 
		h //= 2
		w //= 2
		mip_i += 1
	
	print("\npacked mips")
	# compression blocks are 4x4 pixels
	while h > 2:
		print(mip_i, h, w)
		num_pixels = h * w * header.dx_10.array_size
		num_bytes = num_pixels // pixels_per_byte
		address = stream.tell()
		print(address, num_pixels, num_bytes)
		packed_levels.append( (h, w, stream.read(num_bytes)) )
		h //= 2
		w //= 2
		mip_i += 1

	print("\n packing mips")
	# bytes_per_block =
	
	with io.BytesIO() as packed_writer:
	# with open(dds_file_path+"mip.dds", 'wb') as packed_writer:
		# 1 byte per pixel = 64 px
		# 0.5 bytes per pixel = 128 px
		total_width = 64 * pixels_per_byte
		# pack the last mips into one image
		for i, (height, width, level_bytes) in enumerate(packed_levels):
		
			# write horizontal lines
			
			# get count of h slices, 1 block is 4x4 px
			num_slices_y = height // 4
			num_pad_x = (total_width - width) // 4
			bytes_per_line = len(level_bytes) // num_slices_y
			
			# write the bytes for this line from the mip bytes
			for slice_i in range(num_slices_y):
				# get the bytes that represent the blocks of this line
				sl = level_bytes[ slice_i*bytes_per_line : (slice_i+1)*bytes_per_line ]
				packed_writer.write( sl )
				# fill the line with padding blocks
				for k in range(num_pad_x):
					packed_writer.write( empty_block )
				
		# weird stuff at the end
		for j in range(2):
			# empty line
			for k in range(64 // 4):
				packed_writer.write( empty_block )
			
			# write 4x4 lod
			packed_writer.write( level_bytes )
			
			# pad line
			for k in range(60 // 4):
				packed_writer.write( empty_block )
		# empty line
		for k in range(64 // 4):
			packed_writer.write( empty_block )
		
		# still gotta add one more lod here
		if pixels_per_byte == 2:
			# empty line
			for k in range(16):
				packed_writer.write( empty_block )
			# write 4x4 lod
			packed_writer.write( level_bytes )
			# padding
			for k in range(63):
				packed_writer.write( empty_block )
			
			
		packed_mip_bytes = packed_writer.getvalue()

	out_mips = [ x[2] for x in normal_levels ]
	out_mips.append(packed_mip_bytes)

	# get final merged output bytes
	return b"".join( out_mips )
	

def load_dds(ovl_data, dds_file_path, tex_sized_str_entry):
	# right now simple injection of buffers
	# todo read header data into fragments
	
	# print(dds_file_path, tex_sized_str_entry)
	
	# load dds
	with open(dds_file_path, 'rb') as stream:
		version = DdsFormat.version_number("DX10")
		dds_data = DdsFormat.Data(version=version)
		# no stream, but data version even though that's broken
		header = DdsFormat.Header(stream, dds_data)
		header.read(stream, dds_data)
		# print(header)
		out_bytes = pack_mips_for_jwe(stream, header)
		with open(dds_file_path+"dump.dds", 'wb') as stream:
			header.write(stream, dds_data)
			stream.write(out_bytes)
	
	sum_of_buffers = sum(buffer.size for buffer in tex_sized_str_entry.data_entry.buffers)
	if len(out_bytes) != sum_of_buffers:
		raise BufferError("Packing of MipMaps failed. OVL expects {} bytes, but packing generated {} bytes.".format(len(out_bytes), sum_of_buffers) )
	
	with io.BytesIO(out_bytes) as reader:
		for buffer in tex_sized_str_entry.data_entry.buffers:
			dds_buff = reader.read(buffer.size)
			if len(dds_buff) < buffer.size:
				# print("Missing end",len(dds_buff), buffer.size)
				dds_buff = dds_buff + buffer.data[len(dds_buff):]
			buffer.load_data(dds_buff)
		
def load_mdl2(ovl_data, mdl2_file_path, mdl2_sized_str_entry):
	# read mdl2, find ms2
	# inject ms2 buffers
	# update ms2 + mdl2 fragments
	
	archive = ovl_data.archives[0]
	# these fragments will be overwritten
	model_data_frags = []
	buff_datas = []
	lodinfo = b""
	buffer_info = b""
	mdl2_data = Ms2Format.Data()
	with open(mdl2_file_path, "rb") as mdl2_stream:
		mdl2_data.inspect(mdl2_stream)
		ms2_name = mdl2_data.mdl2_header.name.decode()
		# mdl2_data.read(mdl2_stream, mdl2_data, file=mdl2_file_path, quick=True)
		# print(mdl2_data.mdl2_header)
		for modeldata in mdl2_data.mdl2_header.models:
			# print(modeldata)
			frag_writer = io.BytesIO()
			modeldata.write(frag_writer, data=mdl2_data)
			model_data_frags.append( frag_writer.getvalue() )
			
		frag_writer = io.BytesIO()
		for lod in mdl2_data.mdl2_header.lods:
			lod.write(frag_writer, data=mdl2_data)
			# print(lod)
		lodinfo = frag_writer.getvalue()
		# print(len(lodinfo),lodinfo)
		
	# get ms2 buffers
	dir = os.path.dirname(mdl2_file_path)
	ms2_path = os.path.join(dir, ms2_name)
	with open(ms2_path, "rb") as ms2_stream:
		ms2_header = Ms2Format.Ms2InfoHeader()
		ms2_header.read(ms2_stream, data=mdl2_data)
		
		# get buffer info
		buff_writer = io.BytesIO()
		ms2_header.buffer_info.write(buff_writer, data=mdl2_data)
		buffer_info = buff_writer.getvalue()
	
		# get buffer 0
		buff_writer = io.BytesIO()
		ms2_header.name_hashes.write(buff_writer, data=mdl2_data)
		ms2_header.names.write(buff_writer, data=mdl2_data)
		buff_datas.append( buff_writer.getvalue() )
		
		# get buffer 1
		buff_datas.append( ms2_stream.read(ms2_header.bone_info_size) )
		# get buffer 2
		buff_datas.append( ms2_stream.read() )
		
	# get ms2 sized str entry
	ms2_sized_str_entry = ovl_data.get_sized_str_entry(ms2_name)
	ms2_sized_str_entry.data_entry.load_data(buff_datas)
	
	# get header_data to write into
	writer = archive.headers_data_io[ms2_sized_str_entry.pointers[0].header_index]
	mdl2writer = archive.headers_data_io[mdl2_sized_str_entry.model_data_frags[0].pointers[0].header_index]
	# overwrite mdl2 modeldata frags
	for frag, frag_data in zip(mdl2_sized_str_entry.model_data_frags, model_data_frags):
		mdl2writer.seek(frag.pointers[0].data_offset)
		mdl2writer.write(frag_data)
	
	# overwrite mdl2 lodinfo frag
	mdl2writer.seek(mdl2_sized_str_entry.fragments[1].pointers[1].data_offset)
	mdl2writer.write(lodinfo)
		
	buffer_info_frag = ms2_sized_str_entry.fragments[2]
	header_writer, data_size = archive.get_header_reader(buffer_info_frag, 1)
	# overwrite ms2 buffer info frag
	header_writer.write(buffer_info)
	