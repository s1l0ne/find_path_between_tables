import argparse, json, networkx as nx, pickle

parser = argparse.ArgumentParser(
    description="Найти пути из таблицы A → B"
)
parser.add_argument("source", help="имя таблицы‑источника (в БД)")
parser.add_argument("target", help="имя таблицы‑назначения (в БД)")
parser.add_argument(
    "--graph", '-g', default="graph.gpickle", help="файл с сериализованным графом"
)
parser.add_argument("--maxlen", type=int, default=10, help="макс. длина пути (узлов)")
parser.add_argument(
    "--maxpaths", type=int, default=5, help="макс. выводимых путей"
)
parser.add_argument(
    "--exclude", "-x", nargs="*", default=[],
    help="список узлов (таблиц), которые нужно игнорировать"
)
args = parser.parse_args()

print("Загружаю граф из", args.graph)
with open(args.graph, "rb") as f:
    g_full = pickle.load(f)

if args.source not in g_full:
    quit(f"Таблица '{args.source}' не найдена в графе")
if args.target not in g_full:
    quit(f"Таблица '{args.target}' не найдена в графе")

skip = set(args.exclude)
if args.source in skip or args.target in skip:
    quit("Source/target присутствуют в списке исключений — поиска нет смысла")

missing = skip.difference(g_full.nodes())
if missing:
    print("⚠️  Предупреждение: узлов", ", ".join(missing), "нет в графе и будут пропущены")

g = g_full.copy()
g.remove_nodes_from(skip)
print(f"После исключения узлов граф: |V|={g.number_of_nodes()}, |E|={g.number_of_edges()}")

paths = []
for p in nx.shortest_simple_paths(g, args.source, args.target):
    if len(p) - 1 > args.maxlen:
        continue
    paths.append(p)
    if len(paths) >= args.maxpaths:
        break

if not paths:
    print("Путей не найдено (возможно, все проходили через исключённые узлы",
          "или длина >", args.maxlen, ")")
else:
    more = " (показаны первые {} путей)".format(args.maxpaths) if len(paths) == args.maxpaths else ""
    print(f"Найдено путей: {len(paths)}{more}\n")
    for i, p in enumerate(paths, 1):
        print(f"{i:>3}:  " + " — ".join(p))