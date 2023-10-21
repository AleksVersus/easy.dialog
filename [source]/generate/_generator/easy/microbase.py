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
		# Микробаза сопоставления старых и новых идентификаторов
		self.ids = {}
		self.ids['old'] = []
		self.ids['new'] = []
		# Микробаза сопоставления меток и идентификаторов
		self.ids_mark = {}
		self.ids_mark['ids'] = []
		self.ids_mark['marker'] = []

	def to_qsps(self) -> None:
		for dialog in self.dialogs:
			# перебираем диалоги, и из каждого диалога извлекаем его микробазу
			microbase = dialog.get_microbase()
			# теперь перебираем микробазу диалога, извлекая реплики в микробазу реплик
			for old_id, value in microbase['replic-id'].items():
				new_id = em.Str.random(16, modes={r'\all': True}, exclude='\t ')
				self.id_append(old_id, new_id)
				...

	def id_append(self, old_id:str, new_id:str) -> None:
		self.ids['old'].append(old_id)
		self.ids['new'].append(new_id)
