from __future__ import annotations

import html
import re
import shutil
import subprocess
import tempfile
from datetime import date
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib import colors

from klasbot.config import PRINT_COMMAND, SCHOOL_NAME


def markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    blocks: list[str] = []
    paragraph: list[str] = []
    list_open: str | None = None

    def close_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            blocks.append(f"<p>{inline_markdown(' '.join(paragraph))}</p>")
            paragraph = []

    def close_list() -> None:
        nonlocal list_open
        if list_open:
            blocks.append(f"</{list_open}>")
            list_open = None

    def has_table_pipes(value: str) -> bool:
        return value.count("|") >= 2

    def split_table_row(value: str) -> list[str]:
        return [cell.strip() for cell in value.strip().strip("|").split("|")]

    def is_table_separator(value: str) -> bool:
        cells = split_table_row(value)
        return len(cells) > 1 and all(cell.strip(":").replace("-", "") == "" and "---" in cell for cell in cells)

    def render_table(start_index: int) -> tuple[str, int]:
        headers = split_table_row(lines[start_index])
        rows: list[list[str]] = []
        index = start_index + 2
        while index < len(lines) and lines[index].strip() and has_table_pipes(lines[index]):
            rows.append(split_table_row(lines[index]))
            index += 1
        header_html = "".join(f"<th>{inline_markdown(cell)}</th>" for cell in headers)
        body_rows = []
        for row in rows:
            cells = "".join(f"<td>{inline_markdown(row[column] if column < len(row) else '')}</td>" for column in range(len(headers)))
            body_rows.append(f"<tr>{cells}</tr>")
        return (
            f"<table><thead><tr>{header_html}</tr></thead><tbody>{''.join(body_rows)}</tbody></table>",
            index,
        )

    index = 0
    while index < len(lines):
        raw_line = lines[index]
        line = raw_line.strip()
        if not line:
            close_paragraph()
            close_list()
            index += 1
            continue
        if has_table_pipes(raw_line) and index + 1 < len(lines) and is_table_separator(lines[index + 1]):
            close_paragraph()
            close_list()
            table_html, index = render_table(index)
            blocks.append(table_html)
            continue
        if line.startswith("#"):
            close_paragraph()
            close_list()
            level = min(len(line) - len(line.lstrip("#")), 4)
            blocks.append(f"<h{level}>{inline_markdown(line[level:].strip())}</h{level}>")
        elif line.startswith(("- ", "* ")):
            close_paragraph()
            if list_open != "ul":
                close_list()
                blocks.append("<ul>")
                list_open = "ul"
            blocks.append(f"<li>{inline_markdown(line[2:].strip())}</li>")
        elif re.match(r"^\d+[.)]\s+", line):
            close_paragraph()
            if list_open != "ol":
                close_list()
                blocks.append("<ol>")
                list_open = "ol"
            item_text = re.sub(r"^\d+[.)]\s+", "", line)
            blocks.append(f"<li>{inline_markdown(item_text)}</li>")
        else:
            close_list()
            paragraph.append(line)
        index += 1
    close_paragraph()
    close_list()
    return "\n".join(blocks)


def inline_markdown(value: str) -> str:
    return "".join(
        _math_html(segment["content"], segment["display"])
        if segment["type"] == "math"
        else _inline_text_markdown(segment["content"])
        for segment in _split_math_segments(value)
    )


def _inline_text_markdown(value: str) -> str:
    escaped = html.escape(value)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)
    return escaped


def _math_html(value: str, display: bool) -> str:
    latex = _normalize_latex(value)
    fallback = html.escape(_fallback_latex_text(latex))
    display_value = "true" if display else "false"
    return (
        f'<span class="math-pending" data-display="{display_value}" '
        f'data-latex="{html.escape(latex, quote=True)}">{fallback}</span>'
    )


def _markdown_inline_to_reportlab(value: str) -> str:
    value = _strip_math_to_text(value)
    escaped = html.escape(value)
    escaped = re.sub(r"`([^`]+)`", r"<font face=\"Courier\">\1</font>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", escaped)
    return escaped


def _plain_text(value: str) -> str:
    value = _strip_math_to_text(value)
    return re.sub(r"[*_`#>-]", "", value).strip()


def _split_math_segments(value: str) -> list[dict[str, str | bool]]:
    segments: list[dict[str, str | bool]] = []
    cursor = 0
    delimiters = [
        ("$$", "$$", True),
        (r"\[", r"\]", True),
        (r"\(", r"\)", False),
        ("$", "$", False),
    ]
    while cursor < len(value):
        matches = [
            (value.find(opening, cursor), opening, closing, display)
            for opening, closing, display in delimiters
            if value.find(opening, cursor) >= 0 and not _is_escaped(value, value.find(opening, cursor))
        ]
        if not matches:
            segments.append({"type": "text", "content": value[cursor:], "display": False})
            break
        start_index, opening, closing, display = sorted(matches, key=lambda item: (item[0], -len(item[1])))[0]
        if start_index > cursor:
            segments.append({"type": "text", "content": value[cursor:start_index], "display": False})
        content_start = start_index + len(opening)
        content_end = _find_closing_delimiter(value, closing, content_start)
        if content_end < 0:
            segments.append({"type": "text", "content": _fallback_latex_text(value[start_index:]), "display": False})
            break
        segments.append({"type": "math", "content": value[content_start:content_end], "display": display})
        cursor = content_end + len(closing)
    return segments


def _find_closing_delimiter(value: str, delimiter: str, start: int) -> int:
    index = value.find(delimiter, start)
    while index >= 0 and _is_escaped(value, index):
        index = value.find(delimiter, index + len(delimiter))
    return index


def _is_escaped(value: str, index: int) -> bool:
    slash_count = 0
    cursor = index - 1
    while cursor >= 0 and value[cursor] == "\\":
        slash_count += 1
        cursor -= 1
    return slash_count % 2 == 1


def _normalize_latex(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\\\\", "\\")).strip()


def _fallback_latex_text(value: str) -> str:
    text = _normalize_latex(value)
    text = re.sub(r"\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}", r"\1/\2", text)
    text = re.sub(r"\\sqrt\s*\{([^{}]+)\}", r"sqrt(\1)", text)
    replacements = {
        r"\triangle": "triangle ",
        r"\angle": "angle ",
        r"\times": " x ",
        r"\cdot": " · ",
        r"\div": " / ",
        r"\leq": " <= ",
        r"\le": " <= ",
        r"\geq": " >= ",
        r"\ge": " >= ",
        r"\neq": " != ",
        r"\approx": " approximately ",
        r"\degree": " degrees",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    text = re.sub(r"\\[A-Za-z]+", "", text)
    text = re.sub(r"[{}$]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _strip_math_to_text(value: str) -> str:
    return "".join(
        _fallback_latex_text(str(segment["content"]))
        if segment["type"] == "math"
        else str(segment["content"])
        for segment in _split_math_segments(value)
    )


def export_pdf(content_md: str, metadata: dict | None, target_path: Path) -> Path:
    metadata = metadata or {}
    target_path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    story = []
    title = metadata.get("topic") or metadata.get("title") or "Klasbot Output"
    subject = metadata.get("subject") or ""
    week = f"Week {metadata.get('week_number')}" if metadata.get("week_number") else ""
    meta = " | ".join(value for value in [SCHOOL_NAME, subject, week, date.today().isoformat()] if value)

    story.append(Paragraph(html.escape(title), styles["Title"]))
    story.append(Paragraph(html.escape(meta), styles["Normal"]))
    story.append(Spacer(1, 12))

    lines = content_md.splitlines()
    index = 0
    pending_list: list[str] = []

    def flush_list() -> None:
        nonlocal pending_list
        for item in pending_list:
            story.append(Paragraph(f"&#8226; {_markdown_inline_to_reportlab(item)}", styles["Normal"]))
        if pending_list:
            story.append(Spacer(1, 6))
        pending_list = []

    while index < len(lines):
        raw_line = lines[index]
        line = raw_line.strip()
        if not line:
            flush_list()
            story.append(Spacer(1, 6))
            index += 1
            continue
        if raw_line.count("|") >= 2 and index + 1 < len(lines):
            separator = lines[index + 1].strip()
            if separator.count("|") >= 2 and all("---" in cell for cell in separator.strip("|").split("|")):
                flush_list()
                rows = [[_plain_text(cell) for cell in raw_line.strip("|").split("|")]]
                index += 2
                while index < len(lines) and lines[index].strip() and lines[index].count("|") >= 2:
                    rows.append([_plain_text(cell) for cell in lines[index].strip("|").split("|")])
                    index += 1
                table = Table(rows, repeatRows=1)
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef5f2")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                ]))
                story.append(table)
                story.append(Spacer(1, 8))
                continue
        if line.startswith("#"):
            flush_list()
            level = min(len(line) - len(line.lstrip("#")), 3)
            style_name = "Heading1" if level == 1 else "Heading2" if level == 2 else "Heading3"
            story.append(Paragraph(_markdown_inline_to_reportlab(line[level:].strip()), styles[style_name]))
        elif line.startswith(("- ", "* ")):
            pending_list.append(line[2:].strip())
        elif re.match(r"^\d+[.)]\s+", line):
            pending_list.append(re.sub(r"^\d+[.)]\s+", "", line))
        else:
            flush_list()
            story.append(Paragraph(_markdown_inline_to_reportlab(line), styles["Normal"]))
        index += 1

    flush_list()
    document = SimpleDocTemplate(str(target_path), pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    document.build(story)
    return target_path


def render_print_html(content_md: str, metadata: dict | None = None) -> str:
    metadata = metadata or {}
    title = metadata.get("topic") or metadata.get("title") or "Klasbot Output"
    subject = metadata.get("subject") or ""
    week = f"Week {metadata.get('week_number')}" if metadata.get("week_number") else ""
    today = date.today().isoformat()
    body = markdown_to_html(content_md)
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{html.escape(title)}</title>
    <link rel="stylesheet" href="/static/vendor/katex/katex.min.css" />
    <style>
      @page {{ margin: 18mm; }}
      body {{ font-family: Arial, sans-serif; color: #111; line-height: 1.45; }}
      header {{ border-bottom: 1px solid #999; margin-bottom: 18px; padding-bottom: 8px; }}
      .school {{ font-weight: 700; font-size: 16px; }}
      .meta {{ color: #444; font-size: 12px; margin-top: 4px; }}
      h1 {{ font-size: 24px; margin: 0 0 14px; }}
      h2 {{ font-size: 18px; margin-top: 20px; border-bottom: 1px solid #ddd; }}
      h3 {{ font-size: 15px; margin-top: 16px; }}
      p, li, td, th {{ font-size: 12px; }}
      table {{ width: 100%; border-collapse: collapse; margin: 12px 0 16px; page-break-inside: avoid; }}
      th, td {{ border: 1px solid #aaa; padding: 6px 8px; text-align: left; vertical-align: top; }}
      th {{ background: #eef5f2; font-weight: 700; }}
      code {{ font-family: Consolas, monospace; background: #f2f2f2; padding: 1px 3px; }}
      .math-pending {{ background: #fff7d6; border-radius: 3px; padding: 0 2px; }}
      .katex-display {{ overflow-x: auto; overflow-y: hidden; }}
      footer {{ position: fixed; bottom: 0; left: 0; right: 0; color: #555; font-size: 10px; }}
    </style>
    <script src="/static/vendor/katex/katex.min.js"></script>
  </head>
  <body>
    <header>
      <div class="school">{html.escape(SCHOOL_NAME)}</div>
      <div class="meta">{html.escape(" | ".join(value for value in [subject, title, week, today] if value))}</div>
    </header>
    <main>{body}</main>
    <footer>Generated by Klasbot | {today}</footer>
    <script>
      document.querySelectorAll('[data-latex]').forEach((node) => {{
        if (!window.katex) return;
        try {{
          window.katex.render(node.dataset.latex || '', node, {{
            displayMode: node.dataset.display === 'true',
            throwOnError: false,
            strict: 'ignore',
            output: 'html'
          }});
          node.classList.remove('math-pending');
        }} catch (error) {{
          node.classList.add('math-pending');
        }}
      }});
    </script>
  </body>
</html>"""


def print_html(print_html: str) -> dict:
    command = PRINT_COMMAND
    if not shutil.which(command):
        return {"printed": False, "fallback": True, "reason": f"Print command '{command}' is unavailable"}

    with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8", delete=False) as handle:
        handle.write(print_html)
        temp_path = Path(handle.name)

    try:
        result = subprocess.run(
            [command, str(temp_path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"printed": False, "fallback": True, "reason": str(exc)}
    finally:
        temp_path.unlink(missing_ok=True)

    if result.returncode != 0:
        reason = result.stderr.strip() or result.stdout.strip() or "Print command failed"
        return {"printed": False, "fallback": True, "reason": reason}
    return {"printed": True, "fallback": False, "reason": result.stdout.strip()}
