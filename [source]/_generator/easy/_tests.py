import em

def main():

	# test get num
	text="[count:текст с пробелом] <cord:68> log:непробельные_символы color=#ff8899 tag='многа букав'"

	control = [
		'текст с пробелом', '68', 'непробельные_символы', 'ff8899', 'многа букав', '', 'ff8899'
	]

	output = [
		em.Tag.get_num(text,'count'),	# "текст с пробелом"
		em.Tag.get_num(text,'cord'),	# '68'
		em.Tag.get_num(text,'log'),	# "непробельные_символы"
		em.Tag.get_num(text,'color'),	# "ff8899"
		em.Tag.get_num(text,'tag'),	# "многа букав"
		em.Tag.get_num(text,'tag/h'),	# не выведет ничего
		em.Tag.get_num(text,'color/h')	# "ff8899"
	]

	if control == output: print('Get num is right!')

	# test get cont
	text="[count:текст с пробелом:count] <cord:странный и непонятный текст:cord> log:п р о б е л ь н ы е и непробельные символы:log <color>ff8899</color> [tag]многа букав[/tag]"

	control = [
		'текст с пробелом',
		'странный и непонятный текст',
		'п р о б е л ь н ы е и непробельные символы',
		'ff8899',
		'многа букав'
	]

	output = [
		em.Tag.get_cont(text,'count'),	# "текст с пробелом"
		em.Tag.get_cont(text,'cord'),	# "странный и непонятный текст"
		em.Tag.get_cont(text,'log'),	# "п р о б е л ь н ы е и непробельные символы"
		em.Tag.get_cont(text,'color'),	# "ff8899"
		em.Tag.get_cont(text,'tag')	# "многа букав"
	]

	if control == output: print('Get Cont is right!')


if __name__ == '__main__':
	main()