import argparse, pickle, networkx as nx, sys

p = argparse.ArgumentParser(description="Поиск путей или соседей таблицы")
p.add_argument("source", help="таблица‑A (имя в БД)")
p.add_argument("target", nargs="?", help="таблица‑B (опционально)")
p.add_argument("--graph", default="graph.pickle", help="файл с графом")
p.add_argument("--maxlen", type=int, default=10, help="макс. длина пути (узлов)")
p.add_argument("--maxpaths", type=int, default=5, help="макс. путей к выводу")
p.add_argument("-x", "--exclude", nargs="*", default=[], help="узлы, которые игнорируем")
args = p.parse_args()

with open(args.graph, "rb") as f:
    g_full = pickle.load(f)

if args.source not in g_full:
    sys.exit(f"Ошибка: узла '{args.source}' нет в графе")

if args.target and args.target not in g_full:
    sys.exit(f"Ошибка: узла '{args.target}' нет в графе")

skip = set(args.exclude)
if args.source in skip or (args.target and args.target in skip):
    sys.exit("Source/target присутствуют в списке исключений — прекращаю")

g = g_full.copy()
g.remove_nodes_from(skip)

if args.target is None:
    neigh = sorted(g.neighbors(args.source))
    if not neigh:
        print(f"У {args.source} нет соседних таблиц (после исключений)")
        sys.exit(0)
    print(f"Из {args.source} можно уйти в ({len(neigh)}):\n")
    for n in neigh:
        def_file = g.nodes[n].get("def_file") or "—"
        print(f"  • {n:<25}  файл: {def_file.split('.')[0]}")
    sys.exit(0)

paths = []
for path in nx.shortest_simple_paths(g, args.source, args.target):
    if len(path) - 1 > args.maxlen:
        continue
    paths.append(path)
    if len(paths) >= args.maxpaths:
        break

if not paths:
    print("Путей не найдено (или они длиннее", args.maxlen, ")")
else:
    cap = f"Найдено путей: {len(paths)}"
    if len(paths) == args.maxpaths:
        cap += f"  (показаны первые {args.maxpaths})\n"
    print(cap)
    for i, pth in enumerate(paths, 1):
        print(f"{i:>3}: " + " — ".join(pth))
