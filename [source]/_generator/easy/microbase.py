import os

import pandas

from . import em
from .dialog import EasyDialog
from typing import (List, Dict)

class DialogsBase:
	"""
		Microbase for all dialogs in Easy Dialog's Generator.
	"""
	def __init__(self,
				dialogs:List[str],
				split_code:int=0,
				output_path:str=".\\dialogs_table.qsps"
			) -> None:
		"""
			Replics DataTable Columns
			dialogs - list of the paths to dialogs files (dialogs in edsynt format)
			split_code - if not 0, replics split on `if args[0] = <split_code>` constructions
				for use in cycled filling of dialog
		"""
		self.output_path:str = os.path.abspath(output_path)
		self.split_code:int = split_code
		# извлекаем диалоги в список для последующего конвертирования
		self.dialogs:List[EasyDialog] = []
		for d_path in dialogs:
			self.dialogs.append(EasyDialog(d_path))
		# формируем микробазу для реплик
		self.replics:Dict[str, List[str]] = {}
		self.replics['ids'] = []		# уникальный идентификатор реплики
		self.replics['source'] = []		# фраза, фразовый блок, или обёртка фразы
		self.replics['position'] = []	# идентификатор родителя
		self.replics['includes'] = []	# реплики, вложенные в текущую
		self.replics['run'] = []		# динамический код, или обёртка выводимого действия
		self.replics['type'] = []		# тип реплики
		self.replics['sets'] = []		# настройки реплики	
		# табличка сопоставления старых и новых идентификаторов
		self.ids:Dict[List[str]] = {}
		self.ids['old'] = ['']
		self.ids['new'] = ['']
		# табличка сопоставления меток и идентификаторов
		self.ids_mark:Dict[List[str]] = {}
		self.ids_mark['ids'] = ['']
		self.ids_mark['marker'] = ['']

	def to_qsps(self) -> None:
		""" Convert edg to qsps. """
		self.fill_replics_table() # заполняем общую микробазу реплик
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
		""" Generate qsps-code from dialogs """
		output_lines = []
		unique_ids = []
		output_lines.append(f"QSP-Game Таблица диалогов\n")
		output_lines.append(f'# dialogs_table\n')
		count = 0
		args_count = 0
		for i, old_id in enumerate(self.replics['ids']):
			if self.split_code > 0:
				if count == 0: output_lines.append(f'if args[0] = {args_count}:\n')
				count += 1
			output_lines.append(f'\t!@ REPLIC_{i}\n')
			new_id = self.get_new_id(old_id)
			if self.replics['type'][i] == 'dialog': unique_ids.append((old_id, new_id))
			output_lines.append(f"\t$dialogs_id['{new_id}'] = '{new_id}'\n")
			if self.replics['type'][i] == 'role':
				output_lines.append(f"\t$dialogs_body['{new_id}'] = {{{em.Str.widetrim(self.replics['source'][i], strip=True)}}}\n")
			elif '<frase_block>' in self.replics['source'][i]:
				self.replics['source'][i] = self.frase_block_proced(self.replics['source'][i])
				output_lines.append(f"\t$dialogs_body['{new_id}'] = '{em.Str.widetrim(self.replics['source'][i], strip=True)}'\n")
			else:
				output_lines.append(f"\t$dialogs_body['{new_id}'] = '{em.Str.widetrim(self.replics['source'][i], strip=True)}'\n")
			settings = self.replic_proced_sets(self.replics['sets'][i].strip()).replace("'", "''")
			output_lines.append(f"\t$dialogs_sets['{new_id}'] = '{settings}'\n")
			output_lines.append(f"\tdialogs_count['{new_id}'] = 0\n")
			pos = self.get_new_id(self.replics['position'][i])
			output_lines.append(f"\t$dialogs_position['{new_id}'] = '{pos}'\n")
			includes = list(map(lambda x: self.get_new_id(x), self.replics['includes'][i]))
			output_lines.append(f"\t$dialogs_includes['{new_id}'] = '{'|'.join(includes)}'\n")
			output_lines.append(f"\t$dialogs_run['{new_id}'] = {{{em.Str.widetrim(self.replics['run'][i], strip=True)}}}\n")
			if self.split_code > 0:
				if count == self.split_code or i == len(self.replics['ids'])-1:
					output_lines.append(f'end\n')
					count = 0
					args_count += 1
		output_lines.append(f'-- dialogs_table\n')

		output_lines.append(f'\nИнициализация таблицы данных диалогов:\n')
		output_lines.append(f'# dialogs_init\n')
		output_lines.append(f'!@ @edb.init()\n')
		output_lines.append(f"@edb.new_table('dialogs', 'Диалоги')\n")
		output_lines.append(f"@edb.dt.new_col('body', 'str')\n")
		output_lines.append(f"@edb.dt.new_col('sets', 'dict')\n")
		output_lines.append(f"@edb.dt.new_col('count', 'num')\n")
		output_lines.append(f"@edb.dt.new_col('position', 'str')\n")
		output_lines.append(f"@edb.dt.new_col('includes', 'list')\n")
		output_lines.append(f"@edb.dt.new_col('run', 'code')\n")
		output_lines.append(f"$dialogs['primary_keys_type']='[rstr:16]'\n")
		output_lines.append(f"@edb.new_table('dlgrels', 'Реляции для диалогов')\n")
		output_lines.append(f"@edb.dt.new_col('uid', 'str')\n")
		output_lines.append(f"$dlgrels['primary_keys_type']='[rstr:16]'\n")
		for uid in unique_ids:
			output_lines.append(f"$dlgrels_id['{uid[0]}'] = '{uid[0]}' & $dlgrels_uid['{uid[0]}'] = '{uid[1]}'\n")
		output_lines.append(f'-- dialogs_init\n')

		if self.split_code > 0:
			output_lines.append(f'\nЦикл для последовательной подгрузки реплик группами:\n')
			output_lines.append(f'# dialogs_load\n')
			output_lines.append(f'loop local i = 0 while i < {args_count} step i += 1:\n\t@dialogs_table(i)\nend\n')
			output_lines.append(f'-- dialogs_load\n')

		with open(self.output_path, 'w', encoding='utf-8') as fp:
			fp.writelines(output_lines)

	def frase_block_proced(self, source:str) -> str:
		""" replace ids by really ids in frase block """
		frase_block = em.Tag.get_cont(source, 'frase_block').split('\n')
		for i, frase in enumerate(frase_block):
			actor_id = em.Tag.get_num(frase, 'actor')
			if actor_id:
				actor_id = self.get_new_id(actor_id)
				frase_block[i] = em.Tag.del_num(frase, 'actor', rpl=f'<actor:{actor_id}>')
		fb = "\n".join(frase_block)
		return em.Tag.del_cont(source, 'frase_block', rpl=f'<frase_block>{fb}</frase_block>')


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
			if not new_id in self.ids['new']: return new_id

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
			raise ValueError(f'[96]: ID "{old_id}" already exists!')
		self.ids['old'].append(old_id)
		self.ids['new'].append(new_id)

	def marker_append(self, old_id:str, marker:str) -> None:
		if marker in self.ids_mark['marker']:
			raise ValueError(f'[98]: The label "{marker}" already exists!')
		self.ids_mark['marker'].append(marker)
		self.ids_mark['ids'].append(old_id)
			
