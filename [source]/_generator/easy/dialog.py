import os

import re

import pandas

from . import em

class EasyDialog:
	"""
		Easy Dialog Object. Generate all dialog's objects,
		and conclude them to microbase.
	"""
	def __init__(self, dialog_file_path:str) -> None:
		""" Constructor of Dialog's Object """
		self.path = os.path.abspath(dialog_file_path)
		with open(self.path, 'r', encoding='utf-8') as fp:
			self.body = fp.read()
		self.uid = em.Tag.get_num(self.body, 'dialog_usrid')
		if self.uid == '':
			raise Exception('Ошибка! Не указано уникальное название диалога.' + self.path)
		self.tags_source = None
		self.microbase = {
			'replic-source': {},
			'replic-id': {},
			'replic-position': {},
			'replic-marker': {},
			'replic-type': {},
			'replic-settings': {},
			'replic-includes': {},
			'replic-run': {},
		}
		self.root = None # id root (dialog id)
		self.actors = []
		self.mb_lines_count = 0
		# конвертируем диалог в тегированный вид
		self.get_tags_source()
		# помещаем диалог в микробазу
		self.to_microbase()
		# извлекаем роли
		self.roles_extract()
		# заменяем айдишники реплик
		self.ids_replace()
		# генерируем списки дочерних
		self.set_includes()
		# регенерируем настройки
		self.sets_transport()

	def to_qsps(self, qsps_file_path:str) -> None:
		output_lines = []
		output_lines.append(f"QSP-Game Диалог {self.uid}\n")
		output_lines.append(f'# dialog_{self.uid}\n')
		for key, value in self.microbase['replic-id'].items():
			output_lines.append(f'!@ REPLIC_{key}\n')
			output_lines.append(f"$dialogs_id['{value}'] = '{value}'\n")
			if self.microbase['replic-type'][key] == 'role':
				output_lines.append(f"$dialogs_body['{value}'] = {{{em.Str.widetrim(self.microbase['replic-source'][key], strip=True)}}}\n")
			else:
				output_lines.append(f"$dialogs_body['{value}'] = '{em.Str.widetrim(self.microbase['replic-source'][key], strip=True)}'\n")
			output_lines.append(f"$dialogs_sets['{value}'] = '{self.microbase['replic-settings'][key].strip()}'\n")
			output_lines.append(f"dialogs_count['{value}'] = 0\n")
			output_lines.append(f"$dialogs_position['{value}'] = '{self.microbase['replic-position'][key]}'\n")
			output_lines.append(f"$dialogs_includes['{value}'] = '{'|'.join(self.microbase['replic-includes'][key])}'\n")
			output_lines.append(f"$dialogs_run['{value}'] = {{{em.Str.widetrim(self.microbase['replic-run'][key], strip=True)}}}\n")
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
		self.root = str(i)
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
					self.mb_replic_append(bb, source, f'{rtype}{bb}', pos, None, rtype)
					queue.append(bb)
				elif re.search(rf'<answer(\d+)>[\s\S]*<\/answer\1>|<quest(\d+)>[\s\S]*<\/quest\2>', self.microbase['replic-source'][str(i)]) is None:
					break
				bb -= 1
		self.save_temp_file('.\\01_microbase.xlsx', save_temp_file)

	def set_includes(self, save_temp_file=False) -> None:
		for parent_key, parent_value in self.microbase['replic-id'].items():
			# перебираем идентификаторы реплик
			# key - microbase id, value - replic id
			for daughter_key, daughter_value in self.microbase['replic-position'].items():
				if daughter_value == parent_value:
					# если значение в position и id совпадает
					daughter_id = self.microbase['replic-id'][daughter_key]
					self.mb_prop_append('replic-includes', parent_key, daughter_id)
		self.save_temp_file('.\\02_set_includes.xlsx', save_temp_file)
				
	def roles_extract(self, save_temp_file=False) -> None:
		key = self.root
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
				self.actors.append(actor)
				actors[actor] = em.Tag.get_cont(self.microbase['replic-source'][key], f'actor.{actor}')
				self.gen_actor(actor, actors[actor])
				self.microbase['replic-source'][key] = re.sub(f'<(actor.{actor})>'+r'[\s\S]+?<\/\1>', '', self.microbase['replic-source'][key])
				dialog_actors += f'{self.uid}.{actor}|'
				if '<default_active>' in actors[actor]:
					self.microbase['replic-settings'][key] += f'[default_active:{self.uid}.{actor}]\n'
				if '<default_passive>' in actors[actor]:
					self.microbase['replic-settings'][key] += f'[default_passive:{self.uid}.{actor}]\n' 
		self.microbase['replic-settings'][key] += '[actors:' + dialog_actors[:-1] + ':actors]\n'
		strings_count = em.Tag.get_num(self.microbase['replic-source'][key], 'strings')
		self.microbase['replic-source'][key] = re.sub(r'strings:\S+', '', self.microbase['replic-source'][key])
		if strings_count != '':
			self.microbase['replic-settings'][key] += f'[strings:{strings_count}]\n'
		self.microbase['replic-source'][key] = re.sub(r'<!--[\s\S]*?-->', '', self.microbase['replic-source'][key])
		self.save_temp_file('.\\03_role_extract.xlsx', save_temp_file)

	def gen_actor(self, actor_id:str, actor_src:str) -> None:
		"""
			generate of actors rows in dialogs data table
		"""
		role_id = f'{self.uid}.{actor_id}'
		wrap_btn = em.Tag.get_cont(actor_src, r'wrap\.btn')
		actor_src = em.Tag.del_cont(actor_src, r'wrap\.btn')
		wrap_frase = em.Tag.get_cont(actor_src, r'wrap\.frase')
		actor_src = em.Tag.del_cont(actor_src, r'wrap\.frase')
		include_role = em.Tag.get_num(actor_src, 'include_role')
		if include_role != '':
			include_role = (f'{self.uid}.{include_role}' if not '.' in include_role else include_role)
			actor_src = em.Tag.del_num(actor_src, 'include_role', rpl=f'[include_role:{include_role}]')
		actor_src.replace('<default_active', '')
		actor_src.replace('<default_passive>', '')
		number = self.mb_lines_count + 1
		self.mb_replic_append(number, wrap_frase, role_id, self.uid, None, 'role')
		self.mb_change_prop('replic-run', str(number), wrap_btn)
		self.mb_change_prop('replic-settings', str(number), actor_src)

	def sets_transport(self, save_temp_file=False) -> None:
		for key in self.microbase['replic-id'].keys():
			self.extract_sets(key)
		self.save_temp_file('.\\05_sets_transport.xlsx', save_temp_file)


	def extract_sets(self, key:str) -> None:
		self.microbase['replic-settings'][key] = self.microbase['replic-settings'][key].strip()

		repeat = em.Tag.get_num(self.microbase['replic-source'][key], 'repeat')
		if repeat != '':
			self.microbase['replic-settings'][key] += f'[repeat:{repeat}]\n'
			self.microbase['replic-source'][key] = em.Tag.del_num(self.microbase['replic-source'][key], 'repeat')

		shuffle = em.Tag.get_num(self.microbase['replic-source'][key], 'shuffle')
		if shuffle != '':
			self.microbase['replic-settings'][key] += f'[shuffle:{shuffle}]\n'
			self.microbase['replic-source'][key] = em.Tag.del_num(self.microbase['replic-source'][key], 'shuffle')

		btn_length = em.Tag.get_num(self.microbase['replic-source'][key], 'btn_length')
		if btn_length != '':
			self.microbase['replic-settings'][key] += f'[btn_length:{btn_length}]\n'
			self.microbase['replic-source'][key] = em.Tag.del_num(self.microbase['replic-source'][key], 'btn_length')

		actor_act = em.Tag.get_num(self.microbase['replic-source'][key], 'actor_act')
		if actor_act != '':
			actor_act = (f'{self.uid}.{actor_act}' if not '.' in actor_act else actor_act)
			self.microbase['replic-settings'][key] += f'[actor_act:{actor_act}]\n'
			self.microbase['replic-source'][key] = em.Tag.del_num(self.microbase['replic-source'][key], 'actor_act')

		actor_pass = em.Tag.get_num(self.microbase['replic-source'][key], 'actor_pass')
		if actor_pass != '':
			actor_pass = (f'{self.uid}.{actor_pass}' if not '.' in actor_pass else actor_pass)
			self.microbase['replic-settings'][key] += f'[actor_pass:{actor_pass}]\n'
			self.microbase['replic-source'][key] = em.Tag.del_num(self.microbase['replic-source'][key], 'actor_pass')

		actor_this = em.Tag.get_num(self.microbase['replic-source'][key], 'actor_this')
		if actor_this != '':
			actor_this = (f'{self.uid}.{actor_this}' if not '.' in actor_this else actor_this)
			self.microbase['replic-settings'][key] += f'[actor_this:{actor_this}]\n'
			self.microbase['replic-source'][key] = em.Tag.del_num(self.microbase['replic-source'][key], 'actor_this')

		include_role = em.Tag.get_num(self.microbase['replic-source'][key], 'include_role')
		if include_role != '':
			include_role = (f'{self.uid}.{include_role}' if not '.' in include_role else include_role)
			self.microbase['replic-settings'][key] += f'[include_role:{include_role}]\n'
			self.microbase['replic-source'][key] = em.Tag.del_num(self.microbase['replic-source'][key], 'include_role')

		levelup = em.Tag.get_num(self.microbase['replic-source'][key], 'levelup')
		if levelup != '':
			self.microbase['replic-settings'][key] += f'[levelup:{levelup}]\n'
			self.microbase['replic-source'][key] = em.Tag.del_num(self.microbase['replic-source'][key], 'levelup')

		leveljump = em.Tag.get_num(self.microbase['replic-source'][key], 'leveljump')
		if leveljump != '':
			leveljump = (f'{self.uid}.{leveljump}' if not '.' in leveljump else leveljump)
			self.microbase['replic-settings'][key] += f'[leveljump:{leveljump}]\n'
			self.microbase['replic-source'][key] = em.Tag.del_num(self.microbase['replic-source'][key], 'leveljump')

		replic_app = em.Tag.get_num(self.microbase['replic-source'][key], 'replic_app')
		if replic_app != '':
			self.microbase['replic-settings'][key] += f'[replic_app:{replic_app}]\n'
			self.microbase['replic-source'][key] = em.Tag.del_num(self.microbase['replic-source'][key], 'replic_app')

		marker = em.Tag.get_num(self.microbase['replic-source'][key], 'marker')
		if marker != '':
			self.microbase['replic-settings'][key] += f'[marker:{self.uid}.{marker}]\n'
			self.microbase['replic-source'][key] = em.Tag.del_num(self.microbase['replic-source'][key], 'marker')
			if not f'{self.uid}.{marker}' in list(self.microbase['replic-marker'].values()):
				self.mb_change_prop('replic-marker', key, f'{self.uid}.{marker}')
			else:
				raise ValueError(f'[264]: The label "{marker}" already exists! Метка "{marker}" уже существует!')

		btn_name = em.Tag.get_cont(self.microbase['replic-source'][key], 'btn_name')
		if btn_name != '':
			self.microbase['replic-settings'][key] += f'[btn_name:{btn_name}:btn_name]\n'
			self.microbase['replic-source'][key] = em.Tag.del_cont(self.microbase['replic-source'][key], 'btn_name')

		if_ = em.Tag.get_cont(self.microbase['replic-source'][key], 'if')
		if if_ != '':
			self.microbase['replic-settings'][key] += f'<if>{if_}</if>\n'
			self.microbase['replic-source'][key] = em.Tag.del_cont(self.microbase['replic-source'][key], 'if')

		dynamic_code = em.Tag.get_cont(self.microbase['replic-source'][key], 'dynamic_code')
		if dynamic_code != '':
			self.microbase['replic-run'][key] = dynamic_code
			self.microbase['replic-source'][key] = em.Tag.del_cont(self.microbase['replic-source'][key], 'dynamic_code')

		frase_block = em.Tag.get_cont(self.microbase['replic-source'][key], 'frase_block')
		if frase_block != '':
			new_frase_block = f'<frase_block>{self.fb_change_actors(frase_block)}</frase_block>'
			self.microbase['replic-source'][key] = em.Tag.del_cont(self.microbase['replic-source'][key], 'frase_block', rpl=new_frase_block)

		selectact_delete = re.search(r'\bselectact\.delete\b', self.microbase['replic-source'][key])
		if selectact_delete is not None:
			self.microbase['replic-settings'][key] += f'[selrepl.del]\n'
			self.microbase['replic-source'][key] = re.sub(r'\bselectact\.delete\b', '', self.microbase['replic-source'][key])

		selectact_kill = re.search(r'\bselectact\.kill\b', self.microbase['replic-source'][key])
		if selectact_kill is not None:
			self.microbase['replic-settings'][key] += f'[selectact.kill]\n'
			self.microbase['replic-source'][key] = re.sub(r'\bselectact\.kill\b', '', self.microbase['replic-source'][key])

		closeup = re.search(r'\bcloseup\b', self.microbase['replic-source'][key])
		if closeup is not None:
			self.microbase['replic-settings'][key] += f'[closeup]\n'
			self.microbase['replic-source'][key] = re.sub(r'\bcloseup\b', '', self.microbase['replic-source'][key])

		self.microbase['replic-source'][key] = em.Tag.del_cont(self.microbase['replic-source'][key], '<!>')
		self.microbase['replic-settings'][key] += f'[type:{self.microbase["replic-type"][key]}]'
		self.microbase['replic-source'][key] = re.sub(r'<!--[\s\S]*?-->', '', self.microbase['replic-source'][key])

	def fb_change_actors(self, frase_block:str) -> str:
		for actor in self.actors:
			if f'<actor:{actor}>' in frase_block:
				frase_block = frase_block.replace(f'<actor:{actor}>', f'<actor:{self.uid}.{actor}>')
		return frase_block

	def ids_replace(self, save_temp_file=False) -> None:
		ids = []
		for key in self.microbase['replic-id'].keys():
			if self.microbase['replic-id'][key] != self.uid and self.microbase['replic-type'][key] != 'role':
				self.microbase['replic-id'][key] = f'{self.uid}.' + self.microbase['replic-id'][key]
				if self.microbase['replic-position'][key] != self.uid:
					self.microbase['replic-position'][key] = f'{self.uid}.' + self.microbase['replic-position'][key]
		self.save_temp_file('.\\04_ids_replace.xlsx', save_temp_file)

	def mb_replic_append(self, number:int, source:str, rid:str, position:str, marker=None, rtype='') -> None:
		self.microbase['replic-source'][str(number)] = source
		self.microbase['replic-id'][str(number)] = rid
		self.microbase['replic-position'][str(number)] = position
		self.microbase['replic-marker'][str(number)] = (marker if marker is not None else '') 
		self.microbase['replic-type'][str(number)] = rtype
		self.microbase['replic-settings'][str(number)] = ''
		self.microbase['replic-includes'][str(number)] = []
		self.microbase['replic-run'][str(number)] = ''
		if number > self.mb_lines_count:
			self.mb_lines_count = number

	def mb_change_prop(self, prop:str, key:str, value:str) -> None:
		self.microbase[prop][key] = value

	def mb_prop_append(self, prop:str, key:str, value:str) -> None:
		if type(self.microbase[prop][key]) == list:
			self.microbase[prop][key].append(value)

	def mb_find_line(self, prop:str, value:str) -> str:
		for key, value_ in self.microbase[prop].items():
			if value_ == value:
				return key
		return None

	def get_microbase(self) -> dict:
		return self.microbase

	def save_temp_file(self, file_path, save_temp_file):
		if save_temp_file:
			db = pandas.DataFrame(self.microbase)
			db.to_excel(file_path)