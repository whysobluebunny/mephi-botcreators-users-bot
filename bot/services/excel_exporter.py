from datetime import datetime
from pathlib import Path

import openpyxl

from bot.models.export_result import ExportParseResult


class ExcelExporter:
    def build_excel(self, result: ExportParseResult, output_path: Path) -> Path:
        workbook = openpyxl.Workbook()
        sheet_mentions = workbook.active
        sheet_mentions.title = "Mentions"
        sheet_display_names = workbook.create_sheet(title="Display Names")
        sheet_mentions.append(["Дата экспорта", "Username"])
        sheet_display_names.append(["Дата экспорта", "DisplayName"])
        export_date = datetime.utcnow()

        for username in result.mentioned_usernames:
            sheet_mentions.append([export_date, username])

        for display_name in result.chat_names:
            sheet_display_names.append([export_date, display_name])

        sheet_mentions.column_dimensions['A'].width = 20
        sheet_mentions.column_dimensions['B'].width = 25
        sheet_display_names.column_dimensions['A'].width = 20
        sheet_display_names.column_dimensions['B'].width = 25

        if not output_path.parent.exists():
            output_path.parent.mkdir(parents=True, exist_ok=True)

        workbook.save(output_path)
        return output_path
