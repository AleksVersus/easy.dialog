from easy.microbase import DialogsBase

def main() -> None:
	# составляем список диалогов из которых будем формировать таблицу данных
	dialogs_files = [
		'..\\..\\[source.game]\\other\\bar.barmen.edg',
		'..\\..\\[source.game]\\other\\bar.alcoholic.edg',
		'..\\..\\[source.game]\\other\\bar.aragorn.edg',
		'..\\..\\[source.game]\\other\\robbank.edg'
	]
	# Выходной файл
	output_path = "..\\..\\[source.game]\\src\\dialogs_table.qsps"
	# формируем объект БазаДиалогов, и генерируем в нём список объектов диалогов
	eid = DialogsBase(dialogs_files, split_code=10, output_path=output_path)
	# теперь конвертируем диалоги из базы в Таблицу Данных для QSP
	eid.to_qsps()

if __name__ == '__main__':
	import time
	old = time.time()
	main()
	print(time.time() - old)