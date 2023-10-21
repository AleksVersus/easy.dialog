from easy.microbase import DialogsBase

def main() -> None:
	# составляем список диалогов из которых будем формировать базу
	dialogs_files = [
		'dialog.txt'
	]
	# формируем объект БазаДиалогов, и генерируем в нём список объектов диалогов
	eid = DialogsBase(dialogs_files)
	# теперь конвертируем диалоги из базы в Таблицу Данных для QSP
	eid.to_qsps()

if __name__ == '__main__':
	main()