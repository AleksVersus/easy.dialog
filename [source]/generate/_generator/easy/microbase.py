import sys
import os

import random
import re
import json

import pandas

from . import em
from .dialog import EasyDialog

class DialogsBase:
	"""
		Microbase for all dialogs in Easy Dialog's Generator.
	"""
	def __init__(self, dialogs:list) -> None:
		"""
			Replics DataTable Columns
		"""
		# извлекаем диалоги в список для последующего конвертирования
		self.dialogs = []
		for d in dialogs:
			self.dialogs.append(EasyDialog(d))
		# формируем микробазу для реплик
		self.replics = {}
		self.replics['ids'] = []		# уникальный идентификатор реплики
		self.replics['source'] = []		# фраза, фразовый блок, или обёртка фразы
		self.replics['position'] = []	# идентификатор родителя
		self.replics['includes'] = []	# реплики, вложенные в текущую
		self.replics['run'] = []		# динамический код, или обёртка выводимого действия
		self.replics['type'] = []		# тип реплики
		self.replics['sets'] = []		# настройки реплики	
		# self.replic_source = []
		# self.replic_source = []
		# self.replic_source = []
		# self.replic_source = []
		# табличка сопоставления старых и новых идентификаторов
		self.ids = {}
		self.ids['old'] = []
		self.ids['new'] = []
		# табличка сопоставления меток и идентификаторов
		self.ids_mark = {}
		self.ids_mark['ids'] = []
		self.ids_mark['marker'] = []

	def to_qsps(self) -> None:
		for dialog in self.dialogs:
			# перебираем диалоги, и из каждого диалога извлекаем его микробазу
			microbase = dialog.get_microbase()
			# теперь перебираем микробазу диалога, извлекая реплики в микробазу реплик
			for key, old_id in microbase['replic-id'].items():
				new_id = self.new_id()
				self.id_append(old_id, new_id)
				line = self.replic_append(old_id)
				self.replic_change_value('source', line, microbase['replic-source'][key])
				self.replic_change_value('position', line, microbase['replic-position'][key])
				self.replic_change_value('includes', line, microbase['replic-includes'][key])
				self.replic_change_value('run', line, microbase['replic-run'][key])
				self.replic_change_value('type', line, microbase['replic-type'][key])
				self.replic_change_value('sets', line, microbase['replic-settings'][key])
				marker = em.Tag.get_num(microbase['replic-settings'][key], 'marker')
				if marker != '':
					self.marker_append(old_id, marker)

		db = pandas.DataFrame(self.replics)
		db.to_excel('.\\mb_microbase_.xlsx')


	def replic_change_value(self, column:str, line:int, value=None) -> None:
		if value is not None: self.replics[column][line] = value


	def replic_append(self, rid:str) -> int:
		self.replics['ids'].append(rid)
		self.replics['source'].append('')
		self.replics['position'].append('')
		self.replics['includes'].append([])
		self.replics['run'].append('')
		self.replics['type'].append('')
		self.replics['sets'].append('')
		return len(self.replics['ids'])-1

	def new_id(self) -> str:
		""" генерируем уникальный идентификатор реплики """
		while True:
			new_id = em.Str.random(16, modes={r'\all': True}, exclude='\t ')
			if not new_id in self.ids['new']:
				return new_id

	def id_append(self, old_id:str, new_id:str) -> None:
		""" добавляем старый и новый инедекс в табличку сопоставлений """
		self.ids['old'].append(old_id)
		self.ids['new'].append(new_id)

	def marker_append(self, old_id:str, marker:str) -> None:
		if not marker in self.ids_mark['marker']:
			self.ids_mark['marker'].append(marker)
			self.ids_mark['ids'].append(old_id)
		else:
			raise ValueError(f'[98]: The label "{marker}" already exists! Метка "{marker}" уже существует!')
