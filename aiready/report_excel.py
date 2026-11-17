"""Report of an assessment as an Excel workbook, in plain language.

The workbook has four sheets: the summary, the nine checks, what to fix first and the
checklist of the criteria that are not scored. Its texts are in the language of the page model.
"""

from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from aiready.plain_language import PageModel
from aiready.texts import Texts

HEADER_FILL = PatternFill("solid", start_color="0D1B3E")
HEADER_FONT = Font(bold=True, color="FFFFFF")
LABEL_FONT = Font(bold=True)
WRAPPED = Alignment(wrap_text=True, vertical="top")
MAX_WIDTH = 70      # widest column, in characters


def excel_bytes(model: PageModel, texts: Texts) -> bytes:
    """The workbook of the page model, as the bytes of an .xlsx file."""
    workbook = Workbook()
    summary = workbook.active
    summary.title = texts.text("excel.sheet.summary")
    metadata = " ".join(sentence for sentence in (model.source_sentence, model.marking_sentence) if sentence)
    result = " ".join(sentence for sentence in (model.headline, model.summary_note) if sentence)
    versions = texts.text("excel.row.criteria_value", criteria_version=model.criteria_version, tool_version=model.tool_version)
    note = texts.text("footer.disclaimer", criteria_version=model.criteria_version)
    for label, value in (
        ("dataset", model.title), ("publisher", model.publisher), ("address", model.url), ("metadata", metadata),
        ("summary", result), ("group", model.group_note), ("criteria", versions), ("note", note),
    ):
        summary.append([texts.text(f"excel.row.{label}"), value])
    for row in summary.iter_rows():
        row[0].font = LABEL_FONT
    finish_sheet(summary, widths=(18, MAX_WIDTH), header=False)

    yes, no = texts.text("excel.yes"), texts.text("excel.no")
    checks = workbook.create_sheet(texts.text("excel.sheet.checks"))
    checks.append([texts.text(f"excel.col.{column}") for column in
                   ("check", "status", "finding", "action", "kind", "core", "effort", "code", "score", "reason")])
    for check in model.checks:
        checks.append([check.title, check.status_label, check.finding, check.action, check.kind_label,
                       yes if check.core else no, check.effort_label, check.criterion_id, check.score, check.reason])
    finish_sheet(checks, widths=(26, 16, MAX_WIDTH, MAX_WIDTH, 20, 12, 28, 9, 10, 50))

    titles = {check.criterion_id: check.title for check in model.checks}
    fixes = workbook.create_sheet(texts.text("excel.sheet.fixes"))
    fixes.append([texts.text(f"excel.col.{column}") for column in ("order", "check", "action", "effort")])
    for order, item in enumerate(model.fix_first, start=1):
        fixes.append([order, titles[item.criterion_id], item.action, item.note])
    if not model.fix_first:
        fixes.append([None, None, texts.text("fix.none"), None])
    finish_sheet(fixes, widths=(8, 26, MAX_WIDTH, 50))

    checklist = workbook.create_sheet(texts.text("excel.sheet.checklist"))
    checklist.append([texts.text(f"excel.col.{column}") for column in ("question", "if_not", "needs", "core", "code", "done")])
    for needs, items in (("files", model.checklist_files), ("judgement", model.checklist_judgement)):
        for item in items:
            checklist.append([item.question, item.if_not, texts.text(f"checklist.{needs}"), yes if item.core else no,
                              item.criterion_id, None])
    finish_sheet(checklist, widths=(MAX_WIDTH, 50, 24, 12, 9, 22))

    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def finish_sheet(sheet, widths: tuple[int, ...], header: bool = True) -> None:
    """Column widths, wrapped text and a header row. Text is never left to be read as a formula."""
    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = width
    for row in sheet.iter_rows():
        for cell in row:
            cell.alignment = WRAPPED
            if isinstance(cell.value, str):
                cell.data_type = "s"
    if header:
        for cell in sheet[1]:
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
        sheet.freeze_panes = "A2"
