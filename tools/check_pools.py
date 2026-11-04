import sys

sys.path.insert(0, "tools")
from dataset import sources  # noqa: E402
from dataset.queries import PRESIDENTS_QUERY, STATE_DETAIL_QUERY  # noqa: E402

pools = {}
pools["uf"] = sources._clean(sources.sparql(STATE_DETAIL_QUERY))
pools["cidade"] = sources._cities(60)
pools["presidente"] = sources._clean(sources.sparql(PRESIDENTS_QUERY))
for key, label, limit in [("time", "clube de futebol", 12), ("rio", "rio", 12),
                          ("parque", "parque nacional", 12),
                          ("estadio", "estádio de futebol", 12)]:
    pools[key] = sources._by_country(label, limit)
pools["jogador"] = sources.people("futebolista", limit=12,
                                  extra="?item wdt:P54 ?team . ?team wdt:P31 wd:Q6979593 .")

for key, items in pools.items():
    print(f"{key:12s} {len(items):3d}  " + " | ".join(i["name"] for i in items[:6]))
