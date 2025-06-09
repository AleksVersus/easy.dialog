import re, uuid
from random import (randint, choices)

from typing import List

class Str:
	_symbols_cahes:dict = {}

	@staticmethod
	def widetrim(text:str, strip:bool=False) -> str:
		""" Trim texts around empty strings """
		lines = text.split('\n')
		lines = Str.trimmer(lines)
		if strip:
			lines = [line.strip() for line in lines]
		return '\n'.join(lines)
		
	@staticmethod
	def trimmer(em_strs:list) -> list:
		""" Cut first and last strings. """
		em_strs = em_strs[:]
		EMPTIES = re.compile(r'^[\s\n\r\t]*$')
		while em_strs and EMPTIES.match(em_strs[0]):
			del em_strs[0]
		while em_strs and EMPTIES.match(em_strs[-1]):
			del em_strs[-1]
		return em_strs

	@staticmethod
	def random(length:int=8, include:str='', exclude:str='', modes:dict=None) -> str:
		""" Get random string. """
		mode = {
			'decimal': False, r'\d': False,
			'heximal': False, r'\h': False,
			'space': False, r'\s': False,
			r'\w': False,
			'cyrillic': False, r'\я': False,
			'latinic': False, r'\z': False,
			r'\all': False, # \d\h\s\w\я\z together
			'lcase': False, # priority by ucase
			'ucase': False,
			'only-this': False # only symbols from include-arg
		}
		if modes is not None:
			mode.update(modes)
		cache_key = (include, exclude, tuple(sorted(mode.items())))
		if cache_key in Str._symbols_cahes:
			symbols = Str._symbols_cahes[cache_key]
		else:
			chars = {
				'digitals': '1234567890',
				'heximal': '1234567890abcdef',
				'latinic': 'QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm',
				'cyrillic': 'ЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮёйцукенгшщзхъфывапролджэячсмитьбю',
				'signs': r'{}:"<>?!@#$%^&*()_+-=`~[];\',./\|№'
			}
			key_choose = False
			symbols = []
			if mode['only-this']:
				symbols = list(include)
			else:
				if mode[r'\all'] or mode[r'\d'] or mode['decimal'] or mode[r'\w']:
					symbols.extend(list(chars['digitals']))
					key_choose = True
				if mode[r'\all'] or mode[r'\h'] or mode['heximal']:
					symbols.extend(list(chars['heximal']))
					key_choose = True
				if mode[r'\all'] or mode[r'\s'] or mode['space']:
					symbols.extend(list('\t '))
					key_choose = True
				if mode[r'\all'] or mode[r'\w']:
					symbols.append('_')
					key_choose = True
				if mode[r'\all'] or mode[r'\я'] or mode['cyrillic'] or mode[r'\w']:
					symbols.extend(list(chars['cyrillic']))
					key_choose = True
				if mode[r'\all'] or mode[r'\z'] or mode['latinic'] or mode[r'\w']:
					symbols.extend(list(chars['latinic']))
					key_choose = True
				if not key_choose:
					symbols = list(chars['signs'])
					symbols.extend(list(chars['digitals']))
					symbols.extend(list(chars['latinic']))
					symbols.extend(list(chars['cyrillic']))
				symbols.extend(list(include))
			symbols = list(set(filter((lambda char: not char in exclude), symbols)))
			Str._symbols_cahes[cache_key] = symbols
		return ''.join(choices(symbols, k=length))

class Tag:

	@staticmethod
	def get_num_compiles(tag_name:str) -> List[re.Pattern]:
		return [
			(re.compile(r'\['+tag_name+r':([\s\S]*?)\]'), 1), # [tag:any symbols]
			(re.compile(r'<'+tag_name+r':([^\>\<]*?)>'), 1), # <tag:any symbols>
			(re.compile(r'\{'+tag_name+r':([^}{]*?)\}'), 1), # {tag:any symbols}
			(re.compile(r'\('+tag_name+r':([^\(\)]*?)\)'), 1), # (tag:any symbols)
			(re.compile(tag_name + r'\s*=\s*("|\')([\s\S]*?)\1'), 2), # tag="any symbols" # tag='any symbols'
			(re.compile(tag_name + r'(:|=#)([\S]+)'), 2) # tag:non_space_symbols # tag=#non_space_symbols
		]

	@staticmethod
	def get_num(string_line:str, tag_name:str) -> str:
		""" get single-tag's content """
		it_hex, res_num = False, ''	# инициализация локальных переменных
		# если указан ключ /h - в результат можно выводить только шестнадцатеричное число
		if tag_name[-2:] == '/h':
			tag_name = tag_name[:-2]
			it_hex = True

		for compile_, group in Tag.get_num_compiles(tag_name):
			match = compile_.search(string_line)
			if match:
				res_num = match.group(group)
				break

		if it_hex:
			hex_match = re.match(r'^([0-9A-Fa-f\-]+)([\S]*)$', res_num)
			return (hex_match.group(0) if hex_match else '')
		return res_num

	@staticmethod
	def del_num(string_line:str, tag_name:str, rpl:str='') -> str:
		""" delete single-tag's content """
		for compile, _ in Tag.get_num_compiles(tag_name):
			match = compile.search(string_line)
			if match:
				return string_line.replace(match.group(0), rpl)
		return string_line

	@staticmethod
	def get_cont_compiles(tag_name:str) -> List[re.Pattern]:
		return [
			re.compile(r'\['+tag_name+r':([\s\S]+?):'+tag_name+r'\]'), # [tag:any symbols:tag]
			re.compile(r'\('+tag_name+r':([\s\S]+?):'+tag_name+r'\)'), # (tag:any symbols:tag)
			re.compile(r'\['+tag_name+r'\]([\s\S]+?)\[\/'+tag_name+r'\]'), # [tag]any symbols[/tag]
			re.compile(r'<'+tag_name+r':([\s\S]+?):'+tag_name+r'>'), # <tag:any symbols:tag>
			re.compile('<'+tag_name+r'>([\s\S]+?)<\/'+tag_name+'>'), # <tag>any symbols</tag>
			re.compile(tag_name+r':([\s\S]+?):'+tag_name) # tag:any symbols:tag
		]

	@staticmethod
	def get_cont(string_line:str, tag_name:str) -> str:
		""" get doubling tag's content """
		if tag_name in ('<!--!>', '<!>'):
			comment_match = re.search(r'<!--([\s\S]+?)-->', string_line) # содержимое комментария
			if comment_match: return comment_match.group(1)
		for compile in Tag.get_cont_compiles(tag_name):
			match = compile.search(string_line)
			if match: return match.group(1)
		return ''

	@staticmethod
	def del_cont(string_line:str, tag_name:str, rpl:str='') -> str:
		""" delete doubling tag's. """
		if tag_name in ('<!--!>', '<!>'):
			comment_match = re.search(r'<!--([\s\S]+?)-->', string_line) # содержимое комментария
			if comment_match: return string_line.replace(comment_match.group(0), rpl)
		for compile in Tag.get_cont_compiles(tag_name):
			match = compile.search(string_line)
			if match: return string_line.replace(match.group(0), rpl)
		return string_line

def gen_uuid() -> str:
	""" UUID-generator """
	return str(uuid.uuid4()).lower()

def main():
	...
	
if __name__ == "__main__":
	main()