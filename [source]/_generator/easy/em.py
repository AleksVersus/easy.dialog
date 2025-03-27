import re
from random import (randint, choices)

class Str:

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
		key_choose = False
		symbols = []
		if mode['only-this']:
			symbols = list(include)
		else:
			if mode[r'\all'] or mode[r'\d'] or mode['decimal']:
				symbols.extend(list('1234567890'))
				key_choose = True
			if mode[r'\all'] or mode[r'\h'] or mode['heximal']:
				symbols.extend(list('1234567890abcdef'))
				key_choose = True
			if mode[r'\all'] or mode[r'\s'] or mode['space']:
				symbols.extend(list('\t '))
				key_choose = True
			if mode[r'\all'] or mode[r'\w']:
				symbols.extend(list('QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm'))
				symbols.extend(list('ЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮёйцукенгшщзхъфывапролджэячсмитьбю'))
				symbols.extend(list('1234567890_'))
				key_choose = True
			if mode[r'\all'] or mode[r'\я'] or mode['cyrillic']:
				symbols.extend(list('ЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮёйцукенгшщзхъфывапролджэячсмитьбю'))
				key_choose = True
			if mode[r'\all'] or mode[r'\z'] or mode['latinic']:
				symbols.extend(list('QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm'))
				key_choose = True
			if not key_choose:
				symbols = list(r'QWERTYUIOP{}ASDFGHJKL:"ZXCVBNM<>?1234567890')
				symbols.extend(list(r"!@#$%^&*()_+-=`~qwertyuiop[]asdfghjkl;'zxcvbnm,./\|№"))
				symbols.extend(list(r"ёйцукенгшщзхъфывапролджэячсмитьбюЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ"))
			symbols.extend(list(include))
			symbols = list(set(filter((lambda char: not char in exclude), symbols)))
		return ''.join(choices(symbols, k=length))

class Tag:

	@staticmethod
	def get_num(string_line:str, tag_name:str) -> str:
		""" get single-tag's content """
		it_hex, res_num = False, ''	# инициализация локальных переменных
		# если указан ключ /h - в результат можно выводить только шестнадцатеричное число
		if tag_name[-2:] == '/h':
			tag_name = tag_name[:-2]
			it_hex = True
		square_brack_match = re.search(r'\['+tag_name+r':([^][]*?)\]', string_line) # [tag:any symbols]
		angle_brack_match = re.search(r'<'+tag_name+r':([^><]*?)>', string_line) # <tag:any symbols>
		figure_brack_match = re.search(r'\{'+tag_name+r':([^}{}]*?)\}', string_line) # {tag:any symbols}
		round_brack_match = re.search(r'<'+tag_name+r':([^><]*?)>', string_line) # (tag:any symbols)
		quotes_match = re.search(tag_name + r'\s*=\s*("|\')([\s\S]*?)\1', string_line) # tag="any symbols" # tag='any symbols'
		nonspace_match = re.search(tag_name + r'(:|=#)([\S]+)', string_line) # tag:non_space_symbols # tag=#non_space_symbols
		if square_brack_match is not None:
			res_num = square_brack_match.group(1)
		elif angle_brack_match is not None:
			res_num = angle_brack_match.group(1)
		elif figure_brack_match is not None:
			res_num = figure_brack_match.group(1)
		elif round_brack_match is not None:
			res_num = round_brack_match.group(1)
		elif quotes_match is not None:			
			res_num = quotes_match.group(2)
		elif nonspace_match is not None:
			res_num = nonspace_match.group(2)
		if it_hex:
			hex_match = re.match(r'^([0-9A-Fa-f\-]+)([\S]*)$', res_num)
			# если число не шестнадцатеричное, а нам нужно именно оно, возвращаем пустую строку
			if hex_match is None:
				return ''
			else:
				return hex_match.group(0)
		else:
			return res_num

	@staticmethod
	def del_num(string_line:str, tag_name:str, rpl='') -> str:
		""" delete single-tag's content """
		square_brack_match = re.search(r'\['+tag_name+r':([^][]*?)\]', string_line) # [tag:any symbols]
		angle_brack_match = re.search(r'<'+tag_name+r':([^><]*?)>', string_line) # <tag:any symbols>
		figure_brack_match = re.search(r'\{'+tag_name+r':([^}{}]*?)\}', string_line) # {tag:any symbols}
		round_brack_match = re.search(r'<'+tag_name+r':([^><]*?)>', string_line) # (tag:any symbols)
		quotes_match = re.search(tag_name + r'\s*=\s*("|\')([\s\S]*?)\1', string_line) # tag="any symbols" # tag='any symbols'
		nonspace_match = re.search(tag_name + r'(:|=#)([\S]+)', string_line) # tag:non_space_symbols # tag=#non_space_symbols
		if square_brack_match is not None:
			return string_line.replace(square_brack_match.group(0), rpl)
		elif angle_brack_match is not None:
			return string_line.replace(angle_brack_match.group(0), rpl)
		elif figure_brack_match is not None:
			return string_line.replace(figure_brack_match.group(0), rpl)
		elif round_brack_match is not None:
			return string_line.replace(round_brack_match.group(0), rpl)
		elif quotes_match is not None:			
			return string_line.replace(quotes_match.group(0), rpl)
		elif nonspace_match is not None:
			return string_line.replace(nonspace_match.group(0), rpl)
		else:
			return string_line

	@staticmethod
	def get_cont(string_line:str, tag_name:str) -> str:
		comment_match = re.search(r'<!--([\s\S]+?)-->', string_line) # содержимое комментария
		sqdd_match = re.search(r'\['+tag_name+r':([\s\S]+?):'+tag_name+r'\]', string_line) # [tag:any symbols:tag]
		rqdd_match = re.search(r'\('+tag_name+r':([\s\S]+?):'+tag_name+r'\)', string_line) # (tag:any symbols:tag)
		sq_match = re.search(r'\['+tag_name+r'\]([\s\S]+?)\[\/'+tag_name+r'\]', string_line) # [tag]any symbols[/tag]
		add_match = re.search(r'<'+tag_name+r':([\s\S]+?):'+tag_name+r'>', string_line) # <tag:any symbols:tag>
		html_match = re.search('<'+tag_name+r'>([\s\S]+?)<\/'+tag_name+'>', string_line) # <tag>any symbols</tag>
		dd_match = re.search(tag_name+r':([\s\S]+?):'+tag_name, string_line) # tag:any symbols:tag
		if tag_name in ('<!--!>', '<!>') and comment_match is not None:
			return comment_match.group(1)
		elif sqdd_match is not None:
			return sqdd_match.group(1)
		elif rqdd_match is not None:
			return rqdd_match.group(1)
		elif sq_match is not None:
			return sq_match.group(1)
		elif add_match is not None:
			return add_match.group(1)
		elif html_match is not None:
			return html_match.group(1)
		elif dd_match is not None:
			return dd_match.group(1)
		else:
			return ''

	@staticmethod
	def del_cont(string_line:str, tag_name:str, rpl='') -> str:
		comment_match = re.search(r'<!--([\s\S]+?)-->', string_line) # содержимое комментария
		sqdd_match = re.search(r'\['+tag_name+r':([\s\S]+?):'+tag_name+r'\]', string_line) # [tag:any symbols:tag]
		rqdd_match = re.search(r'\('+tag_name+r':([\s\S]+?):'+tag_name+r'\)', string_line) # (tag:any symbols:tag)
		sq_match = re.search(r'\['+tag_name+r'\]([\s\S]+?)\[\/'+tag_name+r'\]', string_line) # [tag]any symbols[/tag]
		add_match = re.search(r'<'+tag_name+r':([\s\S]+?):'+tag_name+r'>', string_line) # <tag:any symbols:tag>
		html_match = re.search('<'+tag_name+r'>([\s\S]+?)<\/'+tag_name+'>', string_line) # <tag>any symbols</tag>
		dd_match = re.search(tag_name+r':([\s\S]+?):'+tag_name, string_line) # tag:any symbols:tag
		if tag_name in ('<!--!>', '<!>') and comment_match is not None:
			return string_line.replace(comment_match.group(0), rpl)
		elif sqdd_match is not None:
			return string_line.replace(sqdd_match.group(0), rpl)
		elif rqdd_match is not None:
			return string_line.replace(rqdd_match.group(0), rpl)
		elif sq_match is not None:
			return string_line.replace(sq_match.group(0), rpl)
		elif add_match is not None:
			return string_line.replace(add_match.group(0), rpl)
		elif html_match is not None:
			return string_line.replace(html_match.group(0), rpl)
		elif dd_match is not None:
			return string_line.replace(dd_match.group(0), rpl)
		else:
			return string_line

def gen_uuid() -> str:
	""" UUID-generator """
	symbols = '0123456789abcdef'
	result = []
	for i in range(36):
		if i in (8, 13, 18, 23):
			result.append('-')
		else:
			result.append(symbols[randint(0, 15)])
	return ''.join(result)

def main():
	text = """    
   
   первая строка 1    
вторая строка 2
   
  третья строка
   
       """
	print(Str.widetrim(text))
	print('>>>')
	print(Str.widetrim(text, True))

if __name__ == "__main__":
	main()