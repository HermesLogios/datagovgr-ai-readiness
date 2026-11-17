"""Summary of an assessment in plain language, as text for the console."""

from aiready.plain_language import PageModel
from aiready.texts import Texts


def plain_text(model: PageModel, texts: Texts) -> str:
    """The summary, the priorities, the nine checks and the checklist, in the language of the texts."""
    metadata = " ".join(sentence for sentence in (model.source_sentence, model.marking_sentence) if sentence)
    lines = [model.title, model.publisher, model.url, metadata, "", model.headline]
    if model.summary_note:
        lines.append(model.summary_note)
    lines += [model.group_note, "", texts.text("fix.title")]
    if model.fix_first:
        lines += [f"  {order}. {item.action} {item.note}".rstrip() for order, item in enumerate(model.fix_first, start=1)]
    else:
        lines.append(f"  {texts.text('fix.none')}")
    lines += ["", texts.text("checks.title")]
    for check in model.checks:
        lines.append(f"  [{check.status_label}] {check.title}: {check.finding}")
        if check.action:
            lines.append(f"      {texts.text('card.action')} {check.action}")
    lines += ["", texts.text("checklist.title")]
    for legend, items in ((texts.text("checklist.files"), model.checklist_files),
                          (texts.text("checklist.judgement"), model.checklist_judgement)):
        lines.append(f"  {legend}")
        lines += [f"    - {item.question}" for item in items]
    lines += ["", texts.text("footer.disclaimer", criteria_version=model.criteria_version)]
    return "\n".join(lines) + "\n"
