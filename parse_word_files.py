from pathlib import Path
import re, json, docx, networkx as nx
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
import pickle

DOC_DIR = Path("D:/WordFiles")
OUT_GRAPH = "graph.gpickle"
OUT_MAP = "caption_map.json"

ru_caption_re = re.compile(r"Таблица\s*:?\s*[«\"]\s*([\s\S]+?)\s*[»\"]", re.I)
db_name_re = re.compile(r"Название\s+в\s+базе\s*[:\u200b]?\s*([A-Za-z0-9_]+)", re.I)
fk_target_re = re.compile(r"«\s*([A-Za-zА-Яа-я0-9_]+)\s*»", re.U)


def iter_blocks(parent):
    for ch in parent.element.body.iterchildren():
        if isinstance(ch, CT_P):
            yield docx.text.paragraph.Paragraph(ch, parent)
        elif isinstance(ch, CT_Tbl):
            yield docx.table.Table(ch, parent)


g = nx.Graph()
map_ru2db = {}

for file in DOC_DIR.glob("*.docx"):
    doc = docx.Document(file)
    ru_caption = db_name = None

    for b in iter_blocks(doc):
        if isinstance(b, docx.text.paragraph.Paragraph):
            txt = b.text.strip()
            if m := ru_caption_re.search(txt):
                ru_caption = re.sub(r"\s+", " ", m.group(1)).strip()
                continue
            if ru_caption and (m := db_name_re.search(txt)):
                db_name = m.group(1)
                map_ru2db[ru_caption] = db_name
                g.add_node(db_name)
                continue
        elif isinstance(b, docx.table.Table) and db_name:
            hdr = [c.text.strip() for c in b.rows[0].cells]
            try:
                idx = next(i for i,h in enumerate(hdr) if "тип" in h.lower())
            except StopIteration:
                idx = 2
            for row in b.rows[1:]:
                cells = [c.text.strip() for c in row.cells]
                note = cells[idx]
                if "внешний ключ" in note.lower() and (m:=fk_target_re.search(note)):
                    ru_tgt = m.group(1).strip()
                    tgt = map_ru2db.get(ru_tgt, ru_tgt)
                    g.add_edge(db_name, tgt)
            ru_caption = db_name = None

print(f"Сохранено: узлов={g.number_of_nodes()}, рёбер={g.number_of_edges()}")

with open(OUT_GRAPH, "wb") as f:
    pickle.dump(g, f)
with open(OUT_MAP, "w", encoding="utf-8") as f:
    json.dump(map_ru2db, f, ensure_ascii=False, indent=2)
print(" →", OUT_GRAPH, "и", OUT_MAP)