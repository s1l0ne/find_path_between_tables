from pathlib import Path
import re, json, pickle, docx, networkx as nx
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P

DOC_DIR = Path("D:/ТаблицыТандем")
OUT_GRAPH = "graph.pickle"
OUT_MAP = "caption_map.json"

ru_caption_re = re.compile(r"Таблица\s*:?\s*[«\"]\s*([\s\S]+?)\s*[»\"]", re.I)
db_name_re = re.compile(r"Название\s+в\s+базе\s*[:\u200b]?\s*([A-Za-z0-9_]+)", re.I)
fk_target_re = re.compile(r"«\s*([A-Za-zА-Яа-я0-9_]+)\s*»", re.U)


def iter_blocks(doc):
    for child in doc.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield docx.text.paragraph.Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            yield docx.table.Table(child, doc)

g = nx.Graph()
caption2db = {}

for file in DOC_DIR.glob("*.docx"):
    ru_caption = db_name = None
    doc = docx.Document(file)

    for blk in iter_blocks(doc):
        if isinstance(blk, docx.text.paragraph.Paragraph):
            txt = blk.text.strip()
            if m := ru_caption_re.search(txt):
                ru_caption = re.sub(r"\s+", " ", m.group(1)).strip()
                continue
            if ru_caption and (m := db_name_re.search(txt)):
                db_name = m.group(1)
                caption2db[ru_caption] = db_name
                # если узел уже есть (как FK), но def_file не заполнен — обновляем
                if db_name in g:
                    if g.nodes[db_name].get("def_file") is None:
                        g.nodes[db_name]["def_file"] = file.name
                else:
                    g.add_node(db_name, def_file=file.name)
                continue

        elif isinstance(blk, docx.table.Table) and db_name:
            hdr = [c.text.strip() for c in blk.rows[0].cells]
            try:
                idx = next(i for i,h in enumerate(hdr) if "тип" in h.lower())
            except StopIteration:
                idx = 2
            for row in blk.rows[1:]:
                cells = [c.text.strip() for c in row.cells]
                note  = cells[idx]
                if "внешний ключ" in note.lower() and (m := fk_target_re.search(note)):
                    ru_tgt = m.group(1).strip()
                    tgt = caption2db.get(ru_tgt, ru_tgt)
                    if tgt not in g:
                        g.add_node(tgt, def_file=None)
                    g.add_edge(db_name, tgt)
            ru_caption = db_name = None

print(f"Сохранено узлов={g.number_of_nodes()}  рёбер={g.number_of_edges()}")

with open(OUT_GRAPH, "wb") as f:
    pickle.dump(g, f)

with open(OUT_MAP, "w", encoding="utf-8") as f:
    json.dump(caption2db, f, ensure_ascii=False, indent=2)

print("→", OUT_GRAPH, "и", OUT_MAP)
