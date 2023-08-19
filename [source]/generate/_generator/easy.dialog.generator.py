import sys
import os

import re
import json

import pandas

class EasyDialog:
	"""
		Easy Dialog Generator. Generate the QSP-code of dialogs
		by Source Code of dialog.
	"""
	def __init__(self, dialog_body:str, unique_user_id:str):
		""" Constructor of Dialog's Object """
		self.body = dialog_body
		self.uid = unique_user_id
		self.tags_source = None
		self.microbase = {
			'replic-source': {},
			'replic-id': {},
			'replic-postion': {},
			'replic-marker': {},
			'replic-type': {}
		}
		self.queue = None
		self.get_tags_source(save_temp_file=True)
		self.to_microbase(save_temp_file=True)

	def get_tags_source(self, save_temp_file=False):
		""" Realisation of 'dialog.inTag' fucntion """
		answer_open = '[:'
		answer_close = ':]'
		quest_open = '{:'
		quest_close = ':}'
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

	def to_microbase(self, save_temp_file=False):
		""" convert dialog from tag_source to microbase """
		body = self.tags_source['dialog-body']
		i = self.tags_source['tags-counter']
		self.queue = []
		# добавляем корневую реплику
		self.mb_replic_append(i, body, self.uid, '', self.uid, 'root')
		while len(self.queue) > 0:
			i = self.queue.pop()
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
				elif re.search(rf'<answer(\d+)>[\s\S]*<\/answer\1>|<quest(\d+)>[\s\S]*<\/quest\2>', self.microbase['replic-source'][str(i)]) is None:
					break
				bb -= 1
		if save_temp_file:
			db = pandas.DataFrame(self.microbase)
			db.to_excel('.\\microbase.xlsx')
			# with open('microbase.json', 'w', encoding='utf-8') as fp:
			# 	json.dump(self.microbase, fp, indent=4, ensure_ascii=False)


	def mb_replic_append(self, number:int, source:str, rid:str, position:str, marker='', rtype=''):
		self.microbase['replic-source'][str(number)] = source
		self.microbase['replic-id'][str(number)] = rid
		self.microbase['replic-postion'][str(number)] = position
		self.microbase['replic-marker'][str(number)] = marker
		self.microbase['replic-type'][str(number)] = rtype
		self.queue.append(number)


def main():
	with open('dialog.txt', 'r', encoding='utf-8') as fp:
		text = fp.read()

	dialog = EasyDialog(text, 'test')

if __name__ == '__main__':
	main()