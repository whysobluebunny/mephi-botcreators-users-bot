from pathlib import Path
from datetime import datetime
import openpyxl
from dataclasses import dataclass


@dataclass
class FinalResult:
    """
    Заглушка для тайп-хинтинга, чтобы код был валидным сам по себе.
    В реальном проекте импортируйте ваш настоящий класс FinalResult.
    """
    mentioned_usernames: list[str]


class ExcelExporter:
    def build_excel(self, result: FinalResult, output_path: Path) -> Path:
        """
        Создает Excel файл

        :param result: Объект FinalResult со списком mentioned_usernames
        :param output_path: Путь, куда сохранить файл (включая имя файла)
        :return: Путь к созданному файлу
        """

        # 1. Создаем книгу и лист
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "Mentions"

        # 2. Добавляем заголовки
        headers = ["Дата экспорта", "Username"]
        sheet.append(headers)

        # 3. Подготавливаем данные
        export_date = datetime.utcnow()

        # 4. Записываем строки
        for username in result.mentioned_usernames:
            # Excel корректно обрабатывает объекты datetime
            sheet.append([export_date, username])

        # (Опционально) Настройка ширины колонок для красоты
        sheet.column_dimensions['A'].width = 20
        sheet.column_dimensions['B'].width = 25

        # 5. Убеждаемся, что директория существует
        if not output_path.parent.exists():
            output_path.parent.mkdir(parents=True, exist_ok=True)

        # 6. Сохраняем файл
        workbook.save(output_path)

        return output_path