import openpyxl
import io


def get_stat_xlsx_file(columns: list[str], data: list[list[str]], numerate: bool = False) -> io.BytesIO:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(['#'] + columns if numerate else columns)
    for index, entry in enumerate(data):
        ws.append([str(index + 1)] + entry if numerate else entry)
    excel_data = io.BytesIO()
    wb.save(excel_data)
    excel_data.seek(0)
    return excel_data