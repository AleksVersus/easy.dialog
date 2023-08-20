import re

def widetrim(text:str, strip=False):
	em_str_widetrim_temp_array = text.split('\n')
	trimmer(em_str_widetrim_temp_array)
	result = ''
	for string in em_str_widetrim_temp_array:
		if strip:
			result += string.strip() + '\n'
		else:
			result += string + '\n'
	return result[0:-1]
	

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