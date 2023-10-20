from easy_lib.easy_dialog import EasyDialog

def main() -> None:
	# инициализируем микробазу и настравиаем иерархию
	dialog = EasyDialog('dialog.txt')
	# # конвертируем диалог в формат qsps
	# dialog.to_qsps('dialogs.qsps')

if __name__ == '__main__':
	main()