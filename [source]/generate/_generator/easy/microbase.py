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
	def __init__(self, dialogs:list, split_code=0) -> None:
		"""
			Replics DataTable Columns
			dialogs - list of the paths to dialogs files (dialogs in edsynt format)
			split_code - if not 0, replics split on `if args[0] = <split_code>` constructions
				for use in cycled filling of dialog
		"""
		# извлекаем диалоги в список для последующего конвертирования
		self.dialogs = []
		for d in dialogs:
			self.dialogs.append(EasyDialog(d[0], d[1]))
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
		self.ids['old'] = ['']
		self.ids['new'] = ['']
		# табличка сопоставления меток и идентификаторов
		self.ids_mark = {}
		self.ids_mark['ids'] = ['']
		self.ids_mark['marker'] = ['']

	def to_qsps(self) -> None:
		self.fill_replics_table(save_temp_file=True) # заполняем общую микробазу реплик
		self.gen_qsps() # генерируем валидный код QSPS

	def fill_replics_table(self, save_temp_file=False) -> None:
		""" filling the microbase of replics """
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

		if save_temp_file:
			pandas.DataFrame(self.replics).to_excel('.\\mb_microbase_.xlsx')
			pandas.DataFrame(self.ids).to_excel('.\\mb_ids_.xlsx')
			pandas.DataFrame(self.ids_mark).to_excel('.\\mb_markers_.xlsx')

	def gen_qsps(self) -> None:
		output_lines = []
		output_lines.append(f"QSP-Game Таблица диалогов\n")
		output_lines.append(f'# dialogs_table\n')
		for i, old_id in enumerate(self.replics['ids']):
			new_id = self.get_new_id(old_id)
			output_lines.append(f'!@ REPLIC_{i}\n')
			output_lines.append(f"$dialogs_id['{new_id}'] = '{new_id}'\n")
			if self.replics['type'][i] == 'role':
				output_lines.append(f"$dialogs_body['{new_id}'] = {{{em.Str.widetrim(self.replics['source'][i], strip=True)}}}\n")
			else:
				output_lines.append(f"$dialogs_body['{new_id}'] = '{em.Str.widetrim(self.replics['source'][i], strip=True)}'\n")
			settings = self.replic_proced_sets(self.replics['sets'][i].strip())
			output_lines.append(f"$dialogs_sets['{new_id}'] = '{settings}'\n")
			output_lines.append(f"dialogs_count['{new_id}'] = 0\n")
			pos = self.get_new_id(self.replics['position'][i])
			output_lines.append(f"$dialogs_position['{new_id}'] = '{pos}'\n")
			includes = list(map(lambda x: self.get_new_id(x), self.replics['includes'][i]))
			output_lines.append(f"$dialogs_includes['{new_id}'] = '{'|'.join(includes)}'\n")
			output_lines.append(f"$dialogs_run['{new_id}'] = {{{em.Str.widetrim(self.replics['run'][i], strip=True)}}}\n")
		output_lines.append(f'- dialog_table\n')
		with open('dialogs_table.qsps', 'w', encoding='utf-8') as fp:
			fp.writelines(output_lines)

	def replic_proced_sets(self, sets:str) -> str:
		""" replace temp ids by really ids """
		single_tags = [
			'include_role',
			'actor_act',
			'actor_pass',
			'actor_this',
			'default_active',
			'default_passive',
		]
		for tag in single_tags:
			extract_id = em.Tag.get_num(sets, tag)
			if extract_id != '':
				extract_id = self.get_new_id(extract_id)
				sets = em.Tag.del_num(sets, tag, rpl=f'[{tag}:{extract_id}]')
		single_tags = [
			'leveljump',
			'replic_app',
			'marker'
		]
		for tag in single_tags:
			marker = em.Tag.get_num(sets, tag)
			if marker != '':
				marker = self.id_by_marker(marker)
				sets = em.Tag.del_num(sets, tag, rpl=f'[{tag}:{marker}]')

		actors = em.Tag.get_cont(sets, 'actors')
		if actors != '':
			actors = self.replace_ids(actors)
			sets = em.Tag.del_cont(sets, 'actors', rpl=f'[actors:{actors}:actors]')

		return sets

	def replace_ids(self, ids:str) -> str:
		return '|'.join(list(map(lambda x: self.get_new_id(x), ids.split('|'))))

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

	def id_by_marker(self, marker:str) -> str:
		if marker in self.ids_mark['marker']:
			return self.get_new_id(self.ids_mark['ids'][self.ids_mark['marker'].index(marker)])
		else:
			raise ValueError(f'[163]: The label "{marker}" not found!')

	def get_new_id(self, old_id:str) -> None:
		if old_id in self.ids['old']:
			return self.ids['new'][self.ids['old'].index(old_id)]
		else:
			raise ValueError(f'Not found old id `{old_id}` of replic!')

	def id_append(self, old_id:str, new_id:str) -> None:
		""" добавляем старый и новый инедекс в табличку сопоставлений """
		if old_id in self.ids['old']:
			raise ValueError(f'[96]: ID "{old_id}" already exists! Идентификатор "{old_id}" уже существует!')
		self.ids['old'].append(old_id)
		self.ids['new'].append(new_id)

	def marker_append(self, old_id:str, marker:str) -> None:
		if marker in self.ids_mark['marker']:
			raise ValueError(f'[98]: The label "{marker}" already exists! Метка "{marker}" уже существует!')
		self.ids_mark['marker'].append(marker)
		self.ids_mark['ids'].append(old_id)
			
