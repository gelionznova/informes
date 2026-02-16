import shutil
import zipfile
import re
from pathlib import Path

DOCX_PATH = Path(r"c:\Users\baike\OneDrive\Documentos\Alcaldia\Tatiana\5-feb-2026\informe\app\docx_templates\INF. GESTION.docx")
BACKUP_PATH = DOCX_PATH.with_suffix(".docx.bak")
TABLE_HEADER_LEFT = "ACTIVIDADES DEL CONTRATO"
TABLE_HEADER_RIGHT = "ACTIVIDADES EJECUTADAS"

if not DOCX_PATH.exists():
    raise SystemExit(f"No existe: {DOCX_PATH}")

if not BACKUP_PATH.exists():
    shutil.copyfile(DOCX_PATH, BACKUP_PATH)

SOURCE_PATH = DOCX_PATH

with zipfile.ZipFile(SOURCE_PATH, "r") as zin:
    files = {name: zin.read(name) for name in zin.namelist()}

xml = files["word/document.xml"].decode("utf-8")

def _strip_xml_text(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    text = re.sub(r"\s+", " ", text)
    return text.strip().upper()

def _is_target_table(tbl_xml: str) -> bool:
    tbl_text = _strip_xml_text(tbl_xml)
    if "OBLIGACIONES_DIRECTAS_ITEMS" in tbl_text or "ACTIVIDAD_EJECUTADA" in tbl_text:
        return True
    if TABLE_HEADER_LEFT in tbl_text and TABLE_HEADER_RIGHT in tbl_text:
        return True
    return False

def find_target_table(document_xml: str) -> tuple[int, int] | None:
    index = 0
    while True:
        start = document_xml.find("<w:tbl", index)
        if start == -1:
            return None
        end = document_xml.find("</w:tbl>", start)
        if end == -1:
            return None
        end += len("</w:tbl>")
        tbl = document_xml[start:end]
        if _is_target_table(tbl):
            return start, end
        index = end

def extract_tc_pr(cell_xml: str) -> str:
    match = re.search(r"<w:tcPr>.*?</w:tcPr>", cell_xml, re.S)
    return match.group(0) if match else ""

def extract_tr_pr(row_xml: str) -> str:
    match = re.search(r"<w:trPr>.*?</w:trPr>", row_xml, re.S)
    return match.group(0) if match else ""

def rebuild_table(tbl_xml: str) -> str | None:
    table_head = tbl_xml.split("<w:tr", 1)[0]
    if not table_head.startswith("<w:tbl"):
        return None

    all_rows = re.findall(r"<w:tr.*?</w:tr>", tbl_xml, re.S)
    if len(all_rows) < 2:
        return None

    header_rows = all_rows[:2]
    row_xml = None
    cells = []
    for candidate in all_rows[2:]:
        candidate_cells = re.findall(r"<w:tc>.*?</w:tc>", candidate, re.S)
        if len(candidate_cells) >= 2:
            row_xml = candidate
            cells = candidate_cells
            break

    if not row_xml:
        for candidate in all_rows:
            candidate_cells = re.findall(r"<w:tc>.*?</w:tc>", candidate, re.S)
            if len(candidate_cells) >= 2:
                row_xml = candidate
                cells = candidate_cells
                break

    if not row_xml:
        return None

    tc_pr_left = extract_tc_pr(cells[0])
    tc_pr_right = extract_tc_pr(cells[1])
    tr_pr = extract_tr_pr(row_xml)

    new_row = (
        "<w:tr>"
        f"{tr_pr}"
        f"<w:tc>{tc_pr_left}"
        "<w:p><w:pPr><w:pStyle w:val=\"TableParagraph\"/></w:pPr>"
        "<w:r><w:t>{% for item in obligaciones_directas_items %}</w:t></w:r>"
        "</w:p>"
        "<w:p><w:pPr><w:pStyle w:val=\"TableParagraph\"/></w:pPr>"
        "<w:r><w:t>{{ loop.index }}. {{ item.actividad_contrato }}</w:t></w:r>"
        "</w:p></w:tc>"
        f"<w:tc>{tc_pr_right}"
        "<w:p><w:pPr><w:pStyle w:val=\"TableParagraph\"/></w:pPr>"
        "<w:r><w:t>{{ item.actividad_ejecutada }}</w:t></w:r>"
        "</w:p>"
        "<w:p><w:pPr><w:pStyle w:val=\"TableParagraph\"/></w:pPr>"
        "<w:r><w:t>{% endfor %}</w:t></w:r>"
        "</w:p></w:tc>"
        "</w:tr>"
    )

    return table_head + "".join(header_rows) + new_row + "</w:tbl>"

def remove_plain_placeholder_paragraphs(xml_text: str, name: str) -> str:
    new_parts = []
    last_index = 0
    name_upper = name.upper()
    for match in re.finditer(r"<w:p[^>]*>.*?</w:p>", xml_text, re.S):
        para = match.group(0)
        plain = re.sub(r"<[^>]+>", "", para)
        plain_upper = plain.upper()
        remove = False
        if "{{" in plain and "}}" in plain and name_upper in plain_upper:
            if "ITEM." not in plain_upper:
                remove = True
        new_parts.append(xml_text[last_index:match.start()])
        if not remove:
            new_parts.append(para)
        last_index = match.end()
    new_parts.append(xml_text[last_index:])
    return "".join(new_parts)

new_xml_parts = []
index = 0
replaced = 0
while True:
    span = find_target_table(xml[index:])
    if not span:
        new_xml_parts.append(xml[index:])
        break
    start, end = span
    start += index
    end += index
    tbl_xml = xml[start:end]
    if _is_target_table(tbl_xml):
        rebuilt = rebuild_table(tbl_xml)
        if rebuilt:
            new_xml_parts.append(xml[index:start])
            new_xml_parts.append(rebuilt)
            replaced += 1
            index = end
            continue
    new_xml_parts.append(xml[index:end])
    index = end

if replaced == 0:
    raise SystemExit("No se encontro la tabla de actividades a reemplazar.")

new_xml = "".join(new_xml_parts)
new_xml = remove_plain_placeholder_paragraphs(new_xml, "obligaciones_directas_items")
new_xml = remove_plain_placeholder_paragraphs(new_xml, "actividad_ejecutada")

files["word/document.xml"] = new_xml.encode("utf-8")

with zipfile.ZipFile(DOCX_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zout:
    for name, data in files.items():
        zout.writestr(name, data)

print("OK")
