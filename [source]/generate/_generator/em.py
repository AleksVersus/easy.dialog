import re
import random

class Str:

	@staticmethod
	def widetrim(text:str, strip=False):
		em_str_widetrim_temp_array = text.split('\n')
		Str.trimmer(em_str_widetrim_temp_array)
		result = ''
		for string in em_str_widetrim_temp_array:
			if strip:
				result += string.strip() + '\n'
			else:
				result += string + '\n'
		return result[0:-1]
		
	@staticmethod
	def trimmer(em_strs:list):
		run_1 = True
		run_2 = True
		while (run_1 or run_2) and len(em_strs)>0:
			first = re.match(r'^[\s\n]*$', em_strs[0])
			last = re.match(r'^[\s\n]*$', em_strs[-1])
			if first is None:
				run_1 = False
			else:
				del em_strs[0]
			if last is None or len(em_strs)==0:
				run_2 = False
			else:
				del em_strs[-1]

	@staticmethod
	def random(length=8, include='', exclude='', modes=None):
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
		symbols, new_symbols = '', ''
		if mode['only-this']:
			symbols = include
		else:
			if mode[r'\all'] or mode[r'\d'] or mode['decimal']:
				symbols += '1234567890'
				key_choose = True
			if mode[r'\all'] or mode[r'\h'] or mode['heximal']:
				symbols += '1234567890abcdef'
				key_choose = True
			if mode[r'\all'] or mode[r'\s'] or mode['space']:
				symbols += '\t '
				key_choose = True
			if mode[r'\all'] or mode[r'\w']:
				symbols += 'QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm'
				symbols += 'ЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮёйцукенгшщзхъфывапролджэячсмитьбю'
				symbols += '1234567890_'
				key_choose = True
			if mode[r'\all'] or mode[r'\я'] or mode['cyrillic']:
				symbols += 'ЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮёйцукенгшщзхъфывапролджэячсмитьбю'
				key_choose = True
			if mode[r'\all'] or mode[r'\z'] or mode['latinic']:
				symbols += 'QWERTYUIOPASDFGHJKLZXCVBNMqwertyuiopasdfghjklzxcvbnm'
				key_choose = True
			if not key_choose:
				symbols = r'QWERTYUIOP{}ASDFGHJKL:"ZXCVBNM<>?1234567890'
				symbols += r"!@#$%^&*()_+-=`~qwertyuiop[]asdfghjkl;'zxcvbnm,./\|№"
				symbols += r"ёйцукенгшщзхъфывапролджэячсмитьбюЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ"
			symbols += include
			while len(symbols)>0:
				temp = symbols[0]
				if not temp in exclude:
					new_symbols += temp
				symbols = symbols.replace(temp, '')
			symbols = new_symbols
		result = ''
		for i in range(length):
			result += str(symbols[random.randint(0, len(symbols)-1)])
		return result

	@staticmethod
	def thin(string:str, sparcity=1, separator=' ', modes=None):
		mode = {
			'up': False,
			'left': False,
			'right': False
		}
		if modes is not None:
			mode.update(modes)
		result = []
		if mode['up']:
			while len(string)>0:
				t = string[len(string)-(sparcity):]
				string = string[0:len(string)-(sparcity)]
				result.append(t)
			result.reverse()
		else:
			while len(string)>0:
				t = string[0:sparcity]
				string = string[sparcity:]
				result.append(t)
		rr = separator.join(result)
		if mode['left']: rr = separator + rr
		if mode['right']: rr += separator
		return rr

def gen_uuid():
	symbols = '0123456789abcdef'
	result = ''
	for i in range(36):
		if i in (8, 13, 18, 23):
			result += '-'
		else:
			result += symbols[random.randint(1, len(symbols)-1)]
	return result

if __name__ == "__main__":
	# t = "    \n   \n	   первая строка 1    \nвторая строка 2\n   \n  третья строка\n   \n       "
	# print([Str.widetrim(t, strip=True)])
	# print(Str.random())	# 'вЗНзГШмf'
	# print(Str.random(16, modes={'decimal':True, 'latinic':True, 'cyrillic':True}))	# 'у1ЭAXВ6чГVЫДJМxD'
	# print(Str.random(16))	# '"i!TОж5wПЬрYхв#а'
	# print(Str.random(16, modes={r'\d':True, r'\z':True, r'\я':True}, include='$ @ !'))	# 'cл4фYЛ7@EnoiЪm А'
	# print(Str.random(16, include='24680', exclude='  ©'))	# 'f!с/ Xsэu\ZlcХ"u'
	# print(Str.thin('профессура'))
	# print(Str.thin('профессура', 1, separator='|'))
	# print(Str.thin('профессура', 1, separator='|', modes={'right':True}))
	# print(Str.thin('профессура', 1, separator='|', modes={'left':True}))
	# print(Str.thin('профессура', 1, separator='|', modes={'left':True, 'right':True}))
	# print(Str.thin('профессура', 3, separator='|'))
	# print(Str.thin('профессура', 3, separator='|', modes={'up':True}))
	# print(Str.thin('профессура', 3, separator='|', modes={'left':True}))
	# print(Str.thin('профессура', 2, separator='|', modes={'right':True}))
	# print(Str.thin('профессура', 1, separator='||', modes={'right':True, 'left':True}))
	...