import sys
import os

import random
import re
import json

import pandas

import em

class EasyDialog:
	"""
		Easy Dialog Generator. Generate the QSP-code of dialogs
		by Source Code of dialog.
	"""
	def __init__(self, dialog_body:str, unique_user_id:str) -> None:
		""" Constructor of Dialog's Object """
		self.body = dialog_body
		self.uid = unique_user_id
		self.tags_source = None
		self.microbase = {
			'replic-source': {}, # to dialog_body
			'replic-id': {},
			'replic-position': {},
			'replic-marker': {},
			'replic-type': {},
			'replic-settings': {},
			'replic-includes': {},
			'replic-run': {},
		}
		self.mb_lines_count = 0
		# конвертируем диалог в тегированный вид
		self.get_tags_source()
		# помещаем диалог в микробазу
		self.to_microbase(save_temp_file=True)
		# генерируем списки дочерних
		self.set_includes()
		# регенерируем настройки
		self.sets_transport(save_temp_file=True)
		# заменяем айдишники реплик
		self.ids_replace(save_temp_file=True)

	def to_qsps(self, qsps_file_path:str) -> None:
		output_lines = []
		output_lines.append(f"QSP-Game Диалог {self.uid}\n")
		output_lines.append(f'# dialog_{self.uid}\n')
		for key, value in self.microbase['replic-id'].items():
			output_lines.append(f'!@ REPLIC_{key}\n')
			output_lines.append(f"$dialogs_id['{value}'] = '{value}'\n")
			output_lines.append(f"$dialogs_body['{value}'] = '{em.Str.widetrim(self.microbase['replic-source'][key], strip=True)}'\n")
			output_lines.append(f"$dialogs_sets['{value}'] = '{self.microbase['replic-settings'][key]}'\n")
			output_lines.append(f"dialogs_count['{value}'] = 0\n")
			output_lines.append(f"$dialogs_position['{value}'] = '{self.microbase['replic-position'][key]}'\n")
			output_lines.append(f"$dialogs_includes['{value}'] = '{'|'.join(self.microbase['replic-includes'][key])}'\n")
		output_lines.append(f'- dialog_{self.uid}\n')
		with open(qsps_file_path, 'w', encoding='utf-8') as fp:
			fp.writelines(output_lines)

	def get_tags_source(self, save_temp_file=False) -> None:
		""" Realisation of 'dialog.inTag' fucntion """
		answer_open = '[:' # activated replic
		answer_close = ':]' # activated replic
		quest_open = '{:' # passived replic
		quest_close = ':}' # passived replic
		tag_regexp = re.compile(r'\[:|:\]|\{:|:\}')

		body = self.body
		# меняем открывающие и закрывающие теги на более развёрнутые
		i = 1 # счётчик
		easy_dialog_temp_var1 = []
		easy_dialog_temp_var2 = []
		while True:
			if len(easy_dialog_temp_var1) == 0: easy_dialog_temp_var1.append(-1)
			# easy_dialog_temp_var1[-1] — номер вхождения последнего открывающего тега
			mid = body[easy_dialog_temp_var1[-1]+1:]
			tag_match = re.search(tag_regexp, mid)
			if tag_match is not None:
				# цикл выполняется пока встречаются теги
				tag_instr = tag_match.start() + len(body) - len(mid) # номер позиции символа, с которого начинается вхождение тега
				if tag_instr < 0:
					raise Exception('Ошибка! Не может быть позиция вхождения меньше нуля.')
				tag_type_temp = body[tag_instr:tag_instr+2]
				if tag_type_temp in (answer_open, quest_open):
					# если тег открывающий, заносим значения в минимассив
					easy_dialog_temp_var1.append(tag_instr)
					easy_dialog_temp_var2.append(tag_type_temp)
				elif tag_type_temp in (answer_close, quest_close):
					# если тег закрывающий
					if (tag_type_temp == answer_close and easy_dialog_temp_var2[-1] == answer_open) or (tag_type_temp == quest_close and easy_dialog_temp_var2[-1] == quest_open):
						# закрывающий и открывающий теги совпадают, подменяем теги
						prev_open = body[0:easy_dialog_temp_var1[-1]]
						post_open = body[easy_dialog_temp_var1[-1]+2:tag_instr]
						post_close = body[tag_instr+2:]
						if tag_type_temp == answer_close: new_tag = 'answer'
						if tag_type_temp == quest_close: new_tag = 'quest'
						body = f"{prev_open}<{new_tag}{i}>{post_open}</{new_tag}{i}>{post_close}"
						del easy_dialog_temp_var1[-1]
						del easy_dialog_temp_var2[-1]
						i+=1
					else:
						# найден закрывающий тег, не совпадающий с открывающим, это ошибка
						raise Exception('Ошибка! Закрывающий тег не соответствует открывающему.' + body[easy_dialog_temp_var1[-1]+14:tag_instr-easy_dialog_temp_var1[-1]-14])
			else:
				# теги перестали встречаться, прерываем цикл
				break
		self.tags_source = { 'dialog-body':body, 'tags-counter': i }
		if save_temp_file:
			with open('dialog.html', 'w', encoding='utf-8') as fp:
				fp.write(self.tags_source['dialog-body']+f'\n{self.tags_source["tags-counter"]}')

	def to_microbase(self, save_temp_file=False) -> None:
		""" convert dialog from tag_source to microbase """
		body = self.tags_source['dialog-body']
		i = self.tags_source['tags-counter']
		queue = []
		# добавляем корневую реплику
		self.mb_replic_append(i, body, self.uid, '', self.uid, 'root')
		queue.append(i)
		while len(queue) > 0:
			i = queue.pop()
			bb = i - 1
			while True:
				betta = re.search(rf'<answer{bb}>[\s\S]*<\/answer{bb}>|<quest{bb}>[\s\S]*<\/quest{bb}>', self.microbase['replic-source'][str(i)])
				if betta is not None:
					if betta.group(0).startswith('<answer'):
						rtype = 'answer'
						source = betta.group(0).replace(f'<answer{bb}>','').replace(f'</answer{bb}>', '')
					elif betta.group(0).startswith('<quest'):
						rtype = 'quest'
						source = betta.group(0).replace(f'<quest{bb}>','').replace(f'</quest{bb}>', '')
					self.microbase['replic-source'][str(i)] = self.microbase['replic-source'][str(i)].replace(betta.group(0), '')
					pos = self.microbase['replic-id'][str(i)]
					self.mb_replic_append(bb, source, f'{rtype}{bb}', pos, '', rtype)
					queue.append(bb)
				elif re.search(rf'<answer(\d+)>[\s\S]*<\/answer\1>|<quest(\d+)>[\s\S]*<\/quest\2>', self.microbase['replic-source'][str(i)]) is None:
					break
				bb -= 1
		if save_temp_file:
			db = pandas.DataFrame(self.microbase)
			db.to_excel('.\\microbase.xlsx')
			# with open('microbase.json', 'w', encoding='utf-8') as fp:
			# 	json.dump(self.microbase, fp, indent=4, ensure_ascii=False)

	def mb_replic_append(self, number:int, source:str, rid:str, position:str, marker='', rtype='') -> None:
		self.microbase['replic-source'][str(number)] = source
		self.microbase['replic-id'][str(number)] = rid
		self.microbase['replic-position'][str(number)] = position
		self.microbase['replic-marker'][str(number)] = marker
		self.microbase['replic-type'][str(number)] = rtype
		self.microbase['replic-settings'][str(number)] = ''
		self.microbase['replic-includes'][str(number)] = []
		self.microbase['replic-run'][str(number)] = ''
		if number > self.mb_lines_count:
			self.mb_lines_count = number

	def mb_change_prop(self, prop:str, key:str, value:str) -> None:
		self.microbase[prop][key] = value

	def sets_transport(self, save_temp_file=False):
		for key, value in self.microbase['replic-id'].items():
			if self.microbase['replic-type'][key] == 'root':
				# имеем дело с настройками диалога. Перерабатываем
				self.dialog_sets_transport(key)



				
	def dialog_sets_transport(self, key:str) -> None:
		# Извлекаем роли
		actors_ids = em.Tag.get_num(self.microbase['replic-source'][key], 'actors').split(';')
		actors_ids = list(map(lambda x: x.strip(), actors_ids))
		# удаляем из исходника список ролей
		self.microbase['replic-source'][key] = re.sub(r'actors\s*=\s*("|\')([\s\S]*?)\1', '', self.microbase['replic-source'][key])
		# составляем словарик ролей
		actors = {}
		# список ролей в настройках
		dialog_actors = ''
		for actor in actors_ids:
			if actor != '':
				actors[actor] = em.Tag.get_cont(self.microbase['replic-source'][key], f'actor.{actor}')
				# TODO self.gen_actor(actor, actors[actor])
				self.microbase['replic-source'][key] = re.sub(f'<(actor.{actor})>'+r'[\s\S]+?<\/\1>', '', self.microbase['replic-source'][key])
				dialog_actors += f'{actor}|'
				if '<default_active>' in actors[actor]:
					self.microbase['replic-settings'][key] += f'[default_active:{actor}]\n'
				if '<default_passive>' in actors[actor]:
					self.microbase['replic-settings'][key] += f'[default_passive:{actor}]\n' 
		self.microbase['replic-settings'][key] += '[actors:' + dialog_actors[:-1] + ':actors]\n'
		strings_count = em.Tag.get_num(self.microbase['replic-source'][key], 'strings')
		self.microbase['replic-source'][key] = re.sub(r'strings:\S+', '', self.microbase['replic-source'][key])
		self.microbase['replic-settings'][key] += f'[strings:{strings_count}]\n'
		self.microbase['replic-source'][key] = re.sub(r'<!--[\s\S]*?-->', '', self.microbase['replic-source'][key])


	def gen_actor(self, actor_id:str, actor_src:str) -> None:
		"""
			generate of actors rows in dialogs data table
		"""
		role_id = f'{self.uid}.{actor_id}'
		wrap_act = em.Tag.get_cont(actor_src, r'wrap\.act')
		actor_src = em.Tag.del_cont(actor_src, r'wrap\.act')
		wrap_frase = em.Tag.get_cont(actor_src, r'wrap\.frase')
		actor_src = em.Tag.del_cont(actor_src, r'wrap\.frase')
		actor_src.replace('<default_active', '')
		actor_src.replace('<default_passive>', '')
		number = self.mb_lines_count + 1
		self.mb_replic_append(number, wrap_frase, role_id, self.uid, '', 'role')
		self.mb_change_prop('replic-run', str(number), wrap_act)
		self.mb_change_prop('replic-settings', str(number), actor_src)

	def set_includes(self) -> None:
		for parent_key, parent_value in self.microbase['replic-id'].items():
			# перебираем идентификаторы реплик
			# key - microbase id, value - replic id
			for daughter_key, daughter_value in self.microbase['replic-position'].items():
				if daughter_value == parent_value:
					# если значение в position и id совпадает
					self.microbase['replic-includes'][parent_key].append(self.microbase['replic-id'][daughter_key])

	def ids_replace(self, save_temp_file=False) -> None:
		ids = []
		for key, value in self.microbase['replic-id'].items():
			old_id = value
			while True:
				# генерируем уникальный идентификатор реплики
				new_id = em.Str.random(16, modes={r'\all': True}, exclude='\t ')
				if not new_id in ids:
					ids.append(new_id)
					# записываем новый вместо старого
					self.mb_change_prop('replic-id', key, new_id)
					break
			# ищем старый в position
			for key_, value_ in self.microbase['replic-position'].items():
				if value_ == old_id:
					self.mb_change_prop('replic-position', key_, new_id)
			# перебираем includes
			for value_ in self.microbase['replic-includes'].values():
				if old_id in value_:
					value_[value_.index(old_id)] = new_id
		if save_temp_file:
			db = pandas.DataFrame(self.microbase)
			db.to_excel('.\\microbase_rids.xlsx')

def main() -> None:
	with open('dialog.txt', 'r', encoding='utf-8') as fp:
		text = fp.read()
	# инициализируем микробазу и настравиаем иерархию
	dialog = EasyDialog(text, 'test')
	# конвертируем диалог в формат qsps
	dialog.to_qsps('dialogs.qsps')

if __name__ == '__main__':
	main()