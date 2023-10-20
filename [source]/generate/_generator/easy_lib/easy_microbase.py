import sys
import os

import random
import re
import json

import pandas

import em

class EasyMicroBase:
	"""
		Microbase for all dialogs in Easy Dialog's Generator.
	"""
	def __init__(self) -> None:
		"""
			Replics DataTable Columns
		"""
		self.source = []
		self.ids = []
		self.position = []
		self.marker = []
		self.type = []
		self.settings = []
		self.includes = []
		self.run = []
		# self.replic_source = []
		# self.replic_source = []
		# self.replic_source = []
		# self.replic_source = []

	def append_replic(self, source:str, replic_id:str, position:str, rtype='') -> None:
		self.source.append(source)
		self.ids.append(replic_id)
		self.position.append(position)
		self.marker.append('')
		self.type.append(rtype)
		self.settings.append('')
		self.includes.append([])
		self.run.append('')

	
