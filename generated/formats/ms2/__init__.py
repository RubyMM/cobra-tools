import os
import io
import time
import traceback

from generated.formats.ms2.compound.JointData import JointData
from generated.formats.ms2.compound.Ms2InfoHeader import Ms2InfoHeader
from generated.formats.ms2.compound.Mdl2InfoHeader import Mdl2InfoHeader
from generated.formats.ms2.compound.Ms2BoneInfo import Ms2BoneInfo
from generated.formats.ms2.compound.Ms2BoneInfoPc import Ms2BoneInfoPc
from generated.formats.ms2.compound.PcModel import PcModel
from generated.formats.ms2.compound.PcBuffer1 import PcBuffer1
from generated.formats.ms2.enum.CollisionType import CollisionType
from generated.formats.ovl.versions import *
from generated.formats.ms2.versions import *
from generated.io import IoFile, BinaryStream
from modules.formats.shared import get_padding_size, assign_versions, get_versions, djb, get_padding


def findall(p, s):
	'''Yields all the positions of
	the pattern p in the string s.'''
	i = s.find(p)
	while i != -1:
		yield i
		i = s.find(p, i + 1)


def findall_diff(s, p0, p1):
	'''Yields all the positions of
	the pattern p in the string s.'''
	i = s.find(p0)
	while i != -1:
		if s[i + 20:i + 24] == p1:
			yield i
		i = s.find(p0, i + 1)


class Ms2File(Ms2InfoHeader, IoFile):

	def __init__(self, ):
		super().__init__()

	def assign_bone_names(self, bone_info):
		try:
			for name_i, bone in zip(bone_info.name_indices, bone_info.bones):
				bone.name = self.buffer_0.names[name_i]
		except:
			print("Names failed...")

	def read_all_bone_infos(self, stream, bone_info_cls):
		# functional for JWE detailobjects.ms2, if joint_data is read
		potential_start = stream.tell()
		self.buffer_1_bytes = stream.read(self.bone_info_size)
		stream.seek(potential_start)
		self.bone_infos = []
		if self.bone_info_size:
			print("mdl2 count", self.general_info.mdl_2_count)
			for i in range(self.general_info.mdl_2_count):
				print(f"BONE INFO {i} starts at {stream.tell()}")
				try:
					bone_info = bone_info_cls()
					bone_info.read(stream)
					self.assign_bone_names(bone_info)
					try:
						self.read_joints(bone_info)
					except:
						print("Joints failed...")
						pass
					self.bone_infos.append(bone_info)
					# print(bone_info)
					print("end of bone info at", stream.tell())
					# last one has no padding, so stop here
					if stream.tell() >= potential_start + self.bone_info_size:
						print(f"Exhausted bone info buffer at {stream.tell()}")
						break
					relative_offset = stream.tell() - potential_start
					# currently no other way to predict the padding, no correlation to joint count
					padding_len = get_padding_size(relative_offset)

					print("padding", padding_len, stream.read(padding_len), "joint count", bone_info.joint_count)
				except Exception as err:
					traceback.print_exc()
					print("Bone info failed")
					print(self.bone_infos)
					break
		stream.seek(potential_start)

	def write_all_bone_infos(self, stream):
		# functional for JWE detailobjects.ms2, if joint_data is read
		bone_infos_start = stream.tell()
		for bone_info_index, bone_info in enumerate(self.bone_infos):
			print(f"BONE INFO {bone_info_index} starts at {stream.tell()}")
			bone_info.write(stream)
			if bone_info_index + 1 < len(self.bone_infos):
				relative_offset = stream.tell() - bone_infos_start
				padding = get_padding(relative_offset)
				print("Writing padding", padding)
				stream.write(padding)
		self.bone_info_size = stream.tell() - bone_infos_start

	def get_bone_info(self, mdl2_index, stream, bone_info_cls, hack=True):
		bone_info = None
		potential_start = stream.tell()
		self.buffer_1_bytes = stream.read(self.bone_info_size)
		stream.seek(potential_start)
		print("Start looking for bone info at", potential_start)
		if hack:
			# self.read_all_bone_infos(stream, bone_info_cls)
			# first get all bytes of the whole bone infos block
			# find the start of each using this identifier
			zero_f = bytes.fromhex("00 00 00 00")
			one_f = bytes.fromhex("00 00 80 3F")
			# prefixes = (zero_f, one_f)
			prefixes = (zero_f,)
			# lion has a 1 instead of a 4
			bone_info_marker_1 = bytes.fromhex("FF FF 00 00 00 00 00 00 01")
			# this alone is not picky enough for mod_f_wl_unq_laboratory_corner_002_dst
			bone_info_marker_4 = bytes.fromhex("FF FF 00 00 00 00 00 00 04")
			# bone_info_marker =   bytes.fromhex("00 00 00 00 00 00 00 00 01")
			# bone_info_markerb =   bytes.fromhex("00 00 00 00 00 00 00 00 04")
			suffixes = (bone_info_marker_1, bone_info_marker_4,)
			# there's 8 bytes before this
			bone_info_starts = []
			for prefix in prefixes:
				for suffix in suffixes:
					bone_info_starts.extend(x - 4 for x in findall(prefix + suffix, self.buffer_1_bytes))

			bone_info_starts = list(sorted(set(bone_info_starts)))
			print("bone_info_starts", bone_info_starts)

			if bone_info_starts:
				idx = mdl2_index
				if idx >= len(bone_info_starts):
					print("reset boneinfo index")
					idx = 0
				bone_info_address = potential_start + bone_info_starts[idx]
				print(f"using bone info {idx} of {len(bone_info_starts)} at address {bone_info_address}")
				stream.seek(bone_info_address)
			else:
				print("No bone info found")
		try:
			bone_info = bone_info_cls()
			bone_info.read(stream)
			for hitcheck in bone_info.joints.hitchecks_pc:
				if hitcheck.type == CollisionType.ConvexHull:
					hitcheck.collider.verts = stream.read_floats((hitcheck.collider.vertex_count, 3))
					# print(hitcheck.collider.verts)
			# print(bone_info)
			end_of_bone_info = stream.tell()
			print("end of bone info at", end_of_bone_info)
		except Exception as err:
			traceback.print_exc()
			print("Bone info failed")
		if bone_info:
			self.assign_bone_names(bone_info)
			try:
				self.read_joints(bone_info)
			except:
				pass
		return bone_info

	def read_joints(self, bone_info):

		for i, x in enumerate(bone_info.struct_7.unknown_list):
			# print(i)
			# print(self.bone_info.bones[x.child], x.child)
			# print(self.bone_info.bones[x.parent], x.parent)
			assert x.zero == 0
			assert x.one == 1
		assert bone_info.one == 1
		assert bone_info.name_count == bone_info.bind_matrix_count == bone_info.bone_count == bone_info.bone_parents_count == bone_info.enum_count
		assert bone_info.zeros_count == 0 or bone_info.zeros_count == bone_info.name_count
		assert bone_info.unk_78_count == 0 and bone_info.unknown_88 == 0 and bone_info.unknownextra == 0
		joints = bone_info.joints
		for joint_info in joints.joint_info_list:
			joint_info.name = joints.joint_names.get_str_at(joint_info.name_offset)
			for hit in joint_info.hit_check:
				hit.name = joints.joint_names.get_str_at(hit.name_offset)
		# print(joints)

		# for ix, li in enumerate((joints.first_list, joints.short_list, joints.long_list)):
		# 	print(f"List {ix}")
		# 	for i, x in enumerate(li):
		# 		print(i)
		# 		print(joints.joint_info_list[x.parent].name, x.parent)
		# 		print(joints.joint_info_list[x.child].name, x.child)

		# if bone_info.joint_count:
		# 	for i, joint_info in zip(joints.joint_indices, joints.joint_info_list):
		# 		usually, this corresponds - does not do for speedtree but does not matter
		# 		if not self.bone_info.bones[i].name == joint_info.name:
		# 			print("WARNING NAMES DON'T MATCH", self.bone_info.bones[i].name, joint_info.name)
		# if bone_info.joint_count:
		# 	for i, bone in zip(joints.bone_indices, self.bone_info.bones):
		# 		print(i, bone.name)
		# 		if i > -1:
		# 			print(joints.joint_info_list[i].name)

	def load(self, filepath, mdl2, quick=False, map_bytes=False, read_bytes=False):
		start_time = time.time()
		# eof = super().load(filepath)

		# extra stuff
		self.bone_info = None
		with self.reader(filepath) as stream:
			self.read(stream)
			# buffer 0 (hashes and names) has been read by the header
			# so eoh = start of buffer 1
			self.eoh = stream.tell()
			print(self)
			print("end of header: ", self.eoh)
			if is_old(self):
				self.pc_buffer1 = stream.read_type(PcBuffer1, (self,))
				print(self.pc_buffer1)
				for i, model_info in enumerate(self.pc_buffer1.model_infos):
					print("\n\nMDL2", i)
					# print(model_info)
					model_info.pc_model = stream.read_type(PcModel, (model_info,))
					print(model_info.pc_model)
					if is_pc(self):
						model_info.pc_model_padding = stream.read(get_padding_size(stream.tell() - self.eoh))

					# try:
					# 	self.bone_info = stream.read_type(Ms2BoneInfo)
					# except Exception as err:
					# 	print("BONE INFO FAILED", err)
					self.bone_info = self.get_bone_info(0, stream, Ms2BoneInfo, hack=False)
					# lod_names = [self.bone_names[lod.bone_index] for lod in model_info.pc_model.lods]
					# print(lod_names)
					# print(self.bone_info)
					if i == mdl2.index:
						break
			else:
				self.read_all_bone_infos(stream, Ms2BoneInfo)
				if self.bone_infos:
					self.bone_info = self.bone_infos[mdl2.bone_info_index]

		# numpy chokes on bytes io objects
		with open(filepath, "rb") as stream:
			stream.seek(self.eoh + self.bone_info_size)
			# get the starting position of buffer #2, vertex & face array
			self.start_buffer2 = stream.tell()
			print("self.start_buffer2", self.start_buffer2)
			if is_old(self):
				print("PC model...")
				if not quick:
					tis_counts = [(m.stream_index, m.uv_offset, m.vertex_count) for m in model_info.pc_model.models]
					tis_counts.sort()
					try:
						count_0 = tis_counts[0][2]
						offset_1 = tis_counts[1][1]
						uv_size = offset_1//count_0
					except:
						print("Guessing uv size failed")
						uv_size = 8
					print("guessed uv size", uv_size)
					print("tis_counts", tis_counts)
					# print("tis_offsets", tis_offsets)
					for i, model_data in enumerate(model_info.pc_model.models):
						print("\nModel", i)
						model_data.populate(self, stream, self.start_buffer2, 512, uv_size)
						print(model_data)
					mdl2.lods = model_info.pc_model.lods
					mdl2.mesh_links = model_info.pc_model.mesh_links
					mdl2.models = model_info.pc_model.models
					mdl2.materials = model_info.pc_model.materials
			else:
				print("vert array start", self.start_buffer2)
				print("tri array start", self.start_buffer2 + self.buffer_info.vertexdatasize)

				if not quick:
					for model in mdl2.models:
						model.populate(self, stream, self.start_buffer2, mdl2.model_info.pack_offset)

				if map_bytes:
					for model in mdl2.models:
						model.read_bytes_map(self.start_buffer2, stream)

				# store binary data for verts and tris on the model
				if read_bytes:
					for model in mdl2.models:
						model.read_bytes(self.start_buffer2, self.buffer_info.vertexdatasize, stream)

	def lookup_material(self, mdl2, models):
		print("mapping")
		for lod_index, lod in enumerate(mdl2.lods):
			lod.mesh_links = mdl2.mesh_links[lod.first_model_index:lod.last_model_index]
			lod.models = tuple(mdl2.models[mesh_link.model_index] for mesh_link in lod.mesh_links)
			print("LOD", lod_index)
			for mesh_link in lod.mesh_links:
				try:
					material = mdl2.materials[mesh_link.material_index]
					material.name = self.buffer_0.names[material.name_index]
					model = models[mesh_link.model_index]
					model.material = material.name
					print(f"Model: {mesh_link.model_index} Material: {material.name} Material Unk: {material.some_index} "
						  f"Lod Index: {model.poweroftwo} Flag: {int(model.flag)}")
				except Exception as err:
					print(err)
					print(f"Couldn't match material {mesh_link.material_index} to model {mesh_link.model_index} - bug?")
					print(len(models), mesh_link, mdl2.materials)

	def update_names(self, mdl2s):
		print("Updating MS2 name buffer")
		self.buffer_0.names.clear()
		for mdl2 in mdl2s:
			for material in mdl2.materials:
				if material.name not in self.buffer_0.names:
					self.buffer_0.names.append(material.name)
				material.name_index = self.buffer_0.names.index(material.name)
			for bone_index, bone in enumerate(self.bone_info.bones):
				if bone.name not in self.buffer_0.names:
					self.buffer_0.names.append(bone.name)
				self.bone_info.name_indices[bone_index] = self.buffer_0.names.index(bone.name)
			# print(self.bone_info.name_indices)
		# print(self.buffer_0.names)
		print("Updating MS2 name hashes")
		# update hashes from new names
		self.general_info.name_count = len(self.buffer_0.names)
		self.buffer_0.name_hashes.resize(len(self.buffer_0.names))
		for name_i, name in enumerate(self.buffer_0.names):
			self.buffer_0.name_hashes[name_i] = djb(name.lower())
		self.update_buffer_0_bytes()

	def update_buffer_0_bytes(self):
		# update self.bone_names_size
		with BinaryStream() as temp_writer:
			assign_versions(temp_writer, get_versions(self))
			temp_writer.ms_2_version = self.general_info.ms_2_version
			self.buffer_0.write(temp_writer)
			self.buffer_0_bytes = temp_writer.getvalue()
			self.bone_names_size = len(self.buffer_0_bytes)

	def save(self, filepath, mdl2):
		print("Writing verts and tris to temporary buffer")
		self.update_names((mdl2,))

		with BinaryStream() as temp_bone_writer:
			assign_versions(temp_bone_writer, get_versions(self))
			temp_bone_writer.ms_2_version = self.general_info.ms_2_version
			self.write_all_bone_infos(temp_bone_writer)
			bone_bytes = temp_bone_writer.getvalue()

		# write each model's vert & tri block to a temporary buffer
		temp_vert_writer = io.BytesIO()
		temp_tris_writer = io.BytesIO()
		for model in mdl2.models:
			# update ModelData struct
			model.vertex_offset = temp_vert_writer.tell()
			model.tri_offset = temp_tris_writer.tell()
			model.vertex_count = len(model.verts)
			model.tri_index_count = len(model.tri_indices) * model.shell_count
			# write data
			model.write_verts(temp_vert_writer)
			model.write_tris(temp_tris_writer)
		# get bytes from IO object
		vert_bytes = temp_vert_writer.getvalue()
		tris_bytes = temp_tris_writer.getvalue()

		# update lod fragment
		print("update lod fragment")
		for lod in mdl2.lods:
			# print(lod)
			# print(lod_models)
			lod.vertex_count = sum(model.vertex_count for model in lod.models)
			lod.tri_index_count = sum(model.tri_index_count for model in lod.models)
			print("lod.vertex_count", lod.vertex_count)
			print("lod.tri_index_count", lod.tri_index_count)
		print("Writing final output")
		# get original header and buffers 0 & 1

		# modify buffer size
		self.buffer_info.vertexdatasize = len(vert_bytes)
		self.buffer_info.facesdatasize = len(tris_bytes)

		# write output ms2
		with self.writer(filepath) as f:
			self.write(f)
			f.write(bone_bytes)
			f.write(vert_bytes)
			f.write(tris_bytes)


class Mdl2File(Mdl2InfoHeader, IoFile):

	def __init__(self, ):
		super().__init__()

	def load(self, filepath, quick=False, map_bytes=False, read_bytes=False):
		start_time = time.time()
		self.file = filepath
		self.dir, self.basename = os.path.split(filepath)
		self.file_no_ext = os.path.splitext(self.file)[0]
		print(f"Loading {self.basename}")
		# read the file
		try:
			eof = super().load(filepath)
		except Exception as err:
			print(err)
			print(self)

		# print(self)
		self.ms2_path = os.path.join(self.dir, self.name)
		self.ms2_file = Ms2File()
		self.ms2_file.load(self.ms2_path, self, quick=quick, map_bytes=map_bytes, read_bytes=read_bytes)

		# set material links
		self.ms2_file.lookup_material(self, self.models)
		print(f"Finished reading in {time.time() - start_time:.2f} seconds!")

	def save(self, filepath):
		exp = "export"
		exp_dir = os.path.join(self.dir, exp)
		os.makedirs(exp_dir, exist_ok=True)

		mdl2_name = os.path.basename(filepath)

		# create name of output ms2
		new_ms2_name = mdl2_name.rsplit(".", 1)[0] + ".ms2"
		ms2_path = os.path.join(exp_dir, new_ms2_name)
		self.ms2_file.save(ms2_path, self)
		# set new ms2 name to mdl2 header
		self.name = new_ms2_name

		# write final mdl2
		mdl2_path = os.path.join(exp_dir, mdl2_name)
		eof = super().save(mdl2_path)


if __name__ == "__main__":
	m = Mdl2File()
	m.load("C:/Users/arnfi/Desktop/rhinos/rhinoblack_female.mdl2")
	m.load("C:/Users/arnfi/Desktop/rhinos/africanelephant_child.mdl2")
	m.load("C:/Users/arnfi/Desktop/rhinos/platypus.mdl2")
	# m.load("C:/Users/arnfi/Desktop/rattle/western_diamondback_rattlesnake.mdl2")
	# m.load("C:/Users/arnfi/Desktop/anteater/giant_anteater.mdl2")
	# m.load("C:/Users/arnfi/Desktop/ele/africanelephant_female.mdl2")
	# m.load("C:/Users/arnfi/Desktop/ostrich/ugcres.mdl2")
	# m.load("C:/Users/arnfi/Desktop/ostrich/ugcres_hitcheck.mdl2")
	# m.load("C:/Users/arnfi/Desktop/anubis/cc_anubis_carf.mdl2")
	# m.load("C:/Users/arnfi/Desktop/anubis/cc_anubis_bogfl.mdl2")
	# m.load("C:/Users/arnfi/Desktop/anubis/cc_anubis_carf_hitcheck.mdl2")
	# m.load("C:/Users/arnfi/Desktop/gharial/gharial_male.mdl2")
	# m = Mdl2File()
	# # m.load("C:/Users/arnfi/Desktop/prim/models.ms2")
	# print(m)
	#
	# idir = "C:/Users/arnfi/Desktop/out"
	# # idir = "C:/Users/arnfi/Desktop/Coding/ovl/export_save/detailobjects"
	# dic = {}
	# name = "nat_grassdune_02.mdl2"
	# name = "nat_groundcover_searocket_patchy_01.mdl2"
	# indices = []
	#
	# for fp in walker.walk_type(idir, "mdl2"):
	# 	if "hitcheck" in fp or "skeleton" in fp or "airliftstraps" in fp:
	# 		continue
	# 	print(fp)
	# 	m.load(fp, quick=True)
# 	# indices.append(m.index)
# 	print(fp)
# 	# print(list(lod.bone_index for lod in m.lods))
# 	# print(m.model_info)
# 	# lod_indices = list(lod.bone_index for lod in m.lods)
# 	flags = list(mo.flag for mo in m.models)
# 	print(flags)
# 	# indices.extend(unk)
# # 		dic[file] = lod_indices
# # 		if file.lower() == name:
# # 			print(m.ms2_file.bone_info)
# # 		# print(m.ms2_file.bone_info)
# # 		print(m.ms2_file.bone_info.name_indices, lod_indices)
# # 		lod_names = [m.ms2_file.bone_names[i-1] for i in lod_indices]
# # 		print(lod_names)
# # print(dic)
# # # print(m.ms2_file.buffer_0.names)
# # for i, n in enumerate(m.ms2_file.buffer_0.names):
# # 	print(i,n)
# # l = dic[name]
# # print(l)
# # print(indices, max(indices))
# # fp = os.path.join(idir, name)
# # m.load(fp, quick=True)
#
# print(set(indices))
