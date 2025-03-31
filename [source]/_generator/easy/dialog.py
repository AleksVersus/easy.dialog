import os

import re
from typing import (Dict, Union, List, Optional)

import pandas

from . import em

SELECTRPL_DELETE = re.compile(r'\bselrepl\.del\b')
SELECTBTN_DELETE = re.compile(r'\bselbtn\.del\b')
SELECTRPL_KILL = re.compile(r'\bselrepl\.kill\b')
CLOSEUP = re.compile(r'\bcloseup\b')

ACTORS_TAG = re.compile(r'actors\s*=\s*("|\')([\s\S]*?)\1')
HTML_REPLIC_TAG = re.compile(r'<answer(\d+)>[\s\S]*<\/answer\1>|<quest(\d+)>[\s\S]*<\/quest\2>')

RE_COMMENT = re.compile(r'<!--[\s\S]*?-->')

class EasyDialog:
	"""
		Easy Dialog Object. Generate all dialog's objects,
		and conclude them to microbase.
	"""
	def __init__(self, dialog_file_path:str) -> None:
		""" Constructor of Dialog's Object """
		self.path:str = os.path.abspath(dialog_file_path)
		with open(self.path, 'r', encoding='utf-8') as fp:
			self.body:str = fp.read()
		self.uid:str = em.Tag.get_num(self.body, 'dialog_usrid')
		if self.uid == '':
			raise Exception(f'Unique dialog name is not specified. {self.path}')
		self.tags_source:Dict[str, Union[str, int]] = {
			'dialog-body': '',
			'tags-counter': 0
		}
		self.microbase:Dict[str, Dict[str, str]] = {
			'replic-source': {},
			'replic-id': {},
			'replic-position': {},
			'replic-marker': {},
			'replic-type': {},
			'replic-settings': {},
			'replic-includes': {},
			'replic-run': {},
		}
		self.dialog_pk:str = None # id root (dialog primary key)
		self.actors:List[str] = []
		self.mb_lines_count:int = 0
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
		output_lines.append(f'-- dialog_{self.uid}\n')
		with open(qsps_file_path, 'w', encoding='utf-8') as fp:
			fp.writelines(output_lines)

	def get_tags_source(self, save_temp_file=False) -> None:
		""" Realisation of 'dialog.inTag' fucntion """
		ANSWER_OPEN = '[:' # activated replic
		ANSWER_CLOSE = ':]' # activated replic
		QUEST_OPEN = '{:' # passived replic
		QUEST_CLOSE = ':}' # passived replic
		tag_regexp = re.compile(r'\[:|:\]|\{:|:\}')

		body = self.body
		# меняем открывающие и закрывающие теги на более развёрнутые
		i:int = 1 # счётчик
		tag_open_indexes:List[int] = [-1] # задаём смещение для первого прохода, чтобы -1 + 1 давало 0
		tag_open_types:List[str] = []
		while True:
			# tag_open_indexes[-1] — позиция вхождения последнего открывающего тега
			tag_match:Optional[re.Match] = tag_regexp.search(body, tag_open_indexes[-1] + 1)
			if not tag_match:
				break
			# цикл выполняется пока встречаются теги
			tag_instr:int = int(tag_match.start()) # позиция символа, с которого начинается вхождение тега
			tag_type_temp:str = str(tag_match.group(0))
			if tag_type_temp in (ANSWER_OPEN, QUEST_OPEN):
				# если тег открывающий, заносим значения в минимассив
				tag_open_indexes.append(tag_instr)
				tag_open_types.append(tag_type_temp)
			elif tag_type_temp in (ANSWER_CLOSE, QUEST_CLOSE):
				# если тег закрывающий
				if tag_open_types and any([
					(tag_type_temp == ANSWER_CLOSE and tag_open_types[-1] == ANSWER_OPEN),
					(tag_type_temp == QUEST_CLOSE and tag_open_types[-1] == QUEST_OPEN)
				]):
					# закрывающий и открывающий теги совпадают, подменяем теги
					prev_open = body[0:tag_open_indexes[-1]]
					post_open = body[tag_open_indexes[-1]+2:tag_instr]
					post_close = body[tag_instr+2:]
					if tag_type_temp == ANSWER_CLOSE: new_tag = 'answer'
					if tag_type_temp == QUEST_CLOSE: new_tag = 'quest'
					body = f"{prev_open}<{new_tag}{i}>{post_open}</{new_tag}{i}>{post_close}"
					del tag_open_indexes[-1]
					del tag_open_types[-1]
					i += 1
				else:
					# найден закрывающий тег, не совпадающий с открывающим, это ошибка
					raise Exception('Ошибка! Закрывающий тег не соответствует открывающему.' + body[tag_open_indexes[-1]+14:tag_instr-tag_open_indexes[-1]-14])
		print(tag_open_indexes, tag_open_types)
		self.tags_source['dialog-body'] = body
		self.tags_source['tags-counter'] = i
		
		if save_temp_file:
			with open('dialog.html', 'w', encoding='utf-8') as fp:
				fp.write(self.tags_source['dialog-body']+f'\n{self.tags_source["tags-counter"]}')

	def to_microbase(self, save_temp_file=False) -> None:
		""" convert dialog from tag_source to microbase """
		body = self.tags_source['dialog-body']
		i = self.tags_source['tags-counter']
		r_source = self.microbase['replic-source']
		queue = []
		# добавляем корневую реплику
		self.mb_replic_append(i, body, self.uid, '', self.uid, 'dialog')
		self.dialog_pk = str(i)
		queue.append(i)
		while queue:
			i = queue.pop()
			bb = i - 1
			while True:
				betta = re.search(rf'<answer{bb}>[\s\S]*<\/answer{bb}>|<quest{bb}>[\s\S]*<\/quest{bb}>', r_source[str(i)])
				if betta is not None:
					if betta.group(0).startswith('<answer'):
						rtype = 'answer'
						source = betta.group(0).replace(f'<answer{bb}>','').replace(f'</answer{bb}>', '')
					elif betta.group(0).startswith('<quest'):
						rtype = 'quest'
						source = betta.group(0).replace(f'<quest{bb}>','').replace(f'</quest{bb}>', '')
					r_source[str(i)] = r_source[str(i)].replace(betta.group(0), '')
					pos = self.microbase['replic-id'][str(i)]
					self.mb_replic_append(bb, source, f'{rtype}{bb}', pos, None, rtype)
					queue.append(bb)
				elif not HTML_REPLIC_TAG.search(r_source[str(i)]):
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
		""" Extract role's objects from source and appends in mb. """
		key = self.dialog_pk
		r_source = self.microbase['replic-source']
		r_settings = self.microbase['replic-settings']
		# Извлекаем роли
		actors_ids = em.Tag.get_num(r_source[key], 'actors').split(';')
		actors_ids = [actor.strip() for actor in actors_ids if actor.strip()]

		r_source[key] = ACTORS_TAG.sub('', r_source[key]) # удаляем из исходника список ролей
		actors = {} # составляем словарик ролей
		dialog_actors = [] # список ролей в настройках

		for actor in actors_ids:
			self.actors.append(actor)
			actors[actor] = em.Tag.get_cont(r_source[key], f'actor.{actor}')
			self.gen_actor(actor, actors[actor])
			r_source[key] = re.sub(f'<(actor.{actor})>'+r'[\s\S]+?<\/\1>', '', r_source[key])
			dialog_actors.append(f'{self.uid}.{actor}')
			if '<default_active>' in actors[actor]:
				r_settings[key] += f'[default_active:{self.uid}.{actor}]\n'
			if '<default_passive>' in actors[actor]:
				r_settings[key] += f'[default_passive:{self.uid}.{actor}]\n' 
		r_settings[key] += '[actors:' + '|'.join(dialog_actors) + ':actors]\n'
		strings_count = em.Tag.get_num(r_source[key], 'strings')
		r_source[key] = re.sub(r'strings:\S+', '', r_source[key])
		if strings_count:
			r_settings[key] += f'[strings:{strings_count}]\n'
		r_source[key] = re.sub(r'<!--[\s\S]*?-->', '', r_source[key])
		self.save_temp_file('.\\03_role_extract.xlsx', save_temp_file)

	def gen_actor(self, actor_id:str, actor_src:str) -> None:
		""" generate of actor's row in dialogs data table. """
		role_id = f'{self.uid}.{actor_id}'
		wrap_btn = em.Tag.get_cont(actor_src, r'wrap\.btn')
		actor_src = em.Tag.del_cont(actor_src, r'wrap\.btn')
		wrap_frase = em.Tag.get_cont(actor_src, r'wrap\.frase')
		actor_src = em.Tag.del_cont(actor_src, r'wrap\.frase')
		include_role = em.Tag.get_num(actor_src, 'include_role')
		if include_role != '':
			include_role = (f'{self.uid}.{include_role}' if not '.' in include_role else include_role)
			actor_src = em.Tag.del_num(actor_src, 'include_role', rpl=f'[include_role:{include_role}]')
		actor_src = actor_src.replace('<default_active>', '').replace('<default_passive>', '')
		number = self.mb_lines_count + 1
		self.mb_replic_append(number, wrap_frase, role_id, self.uid, None, 'role')
		self.mb_change_prop('replic-run', str(number), wrap_btn)
		self.mb_change_prop('replic-settings', str(number), actor_src)

	def sets_transport(self, save_temp_file=False) -> None:
		for key in self.microbase['replic-id'].keys():
			self.extract_sets(key)
		self.save_temp_file('.\\05_sets_transport.xlsx', save_temp_file)


	def extract_sets(self, key:str) -> None:
		""" Extract settings from source-prop and append to settings-prop. """
		r_settings = self.microbase['replic-settings']
		r_source = self.microbase['replic-source']

		r_settings[key] = r_settings[key].strip()
		settings = []

		simple_num_tags = [
			'repeat', 'shuffle', 'btn_length', 'levelup', 'replic_app'
		]

		for tag in simple_num_tags:
			value = em.Tag.get_num(r_source[key], tag)
			if value:
				settings.append(f'[{tag}:{value}]')
				r_source[key] = em.Tag.del_num(r_source[key], tag)

		complex_num_tags = [
			'actor_act', 'actor_pass', 'actor_this', 'include_role', 'leveljump'
		]

		for tag in complex_num_tags:
			value = em.Tag.get_num(r_source[key], tag)
			if value:
				value = (f'{self.uid}.{value}' if not '.' in value else value)
				settings.append(f'[{tag}:{value}]')
				r_source[key] = em.Tag.del_num(r_source[key], tag)

		commands = [
			(SELECTRPL_DELETE, f'[selrepl.del]'),
			(SELECTBTN_DELETE, f'[selbtn.del]'),
			(SELECTRPL_KILL, f'[selrepl.kill]'),
			(CLOSEUP, f'[closeup]')
		]
		
		for old_com, new_com in commands:
			com_exist = old_com.search(r_source[key])
			if com_exist:
				settings.append(new_com)
				r_source[key] = old_com.sub('', r_source[key])

		value = em.Tag.get_cont(r_source[key], 'btn_name')
		if value:
			settings.append(f'[btn_name:{value}:btn_name]')
			r_source[key] = em.Tag.del_cont(r_source[key], 'btn_name')

		marker = em.Tag.get_num(r_source[key], 'marker')
		if marker != '':
			settings.append(f'[marker:{self.uid}.{marker}]')
			r_source[key] = em.Tag.del_num(r_source[key], 'marker')
			if not f'{self.uid}.{marker}' in list(self.microbase['replic-marker'].values()):
				self.mb_change_prop('replic-marker', key, f'{self.uid}.{marker}')
			else:
				raise ValueError(f'[264]: The label "{marker}" already exists!')

		if_ = em.Tag.get_cont(r_source[key], 'if')
		if if_ != '':
			settings.append(f'<if>{if_}</if>')
			r_source[key] = em.Tag.del_cont(r_source[key], 'if')

		dynamic_code = em.Tag.get_cont(r_source[key], 'dynamic_code')
		if dynamic_code != '':
			self.microbase['replic-run'][key] = dynamic_code
			r_source[key] = em.Tag.del_cont(r_source[key], 'dynamic_code')

		frase_block = em.Tag.get_cont(r_source[key], 'frase_block')
		if frase_block != '':
			new_frase_block = f'<frase_block>{self.fb_change_actors(frase_block)}</frase_block>'
			r_source[key] = em.Tag.del_cont(r_source[key], 'frase_block', rpl=new_frase_block)

		settings.append(f'[type:{self.microbase["replic-type"][key]}]')
		r_settings[key] += '\n'.join(settings)
		r_source[key] = em.Tag.del_cont(r_source[key], '<!>')
		r_source[key] = RE_COMMENT.sub('', r_source[key])

	def fb_change_actors(self, frase_block:str) -> str:
		""" Change actors identificators in frases block. """
		for actor in self.actors:
			frase_block = frase_block.replace(f'<actor:{actor}>', f'<actor:{self.uid}.{actor}>')
		return frase_block

	def ids_replace(self, save_temp_file=False) -> None:
		""" Replace counts-ids by randomstring ids. """
		unique_id = self.uid
		r_id = self.microbase['replic-id']
		r_position = self.microbase['replic-position']
		r_type = self.microbase['replic-type']

		for key in r_id.keys():
			if r_id[key] != unique_id and r_type[key] != 'role':
				r_id[key] = f'{unique_id}.{r_id[key]}'
				if r_position[key] != unique_id:
					r_position[key] = f'{unique_id}.{r_position[key]}'
		self.save_temp_file('.\\04_ids_replace.xlsx', save_temp_file)

	def mb_replic_append(self,
			number:int, source:str, rid:str, position:str,
			marker:str=None, rtype:str='') -> None:
		""" Append replic to microbase. """
		key:str = str(number)
		self.microbase['replic-source'][key] = source
		self.microbase['replic-id'][key] = rid
		self.microbase['replic-position'][key] = position
		self.microbase['replic-marker'][key] = (marker if marker else '') 
		self.microbase['replic-type'][key] = rtype
		self.microbase['replic-settings'][key] = ''
		self.microbase['replic-includes'][key] = []
		self.microbase['replic-run'][key] = ''
		if number > self.mb_lines_count:
			self.mb_lines_count = number

	def mb_change_prop(self, prop:str, key:str, value:str) -> None:
		""" Change value for property. """
		self.microbase[prop][key] = value

	def mb_prop_append(self, prop:str, key:str, value:str) -> None:
		""" Append value to list-type property. """
		self.microbase[prop][key].append(value)

	def get_microbase(self) -> Dict[str, Dict[str, str]]:
		return self.microbase

	def save_temp_file(self, file_path, save_temp_file):
		if save_temp_file:
			db = pandas.DataFrame(self.microbase)
			db.to_excel(file_path)