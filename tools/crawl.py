"""Fetch the pt.wikipedia pageview series for every answer in every pool."""
import sys

sys.path.insert(0, "tools")
from dataset.measure import crawl_pageviews  # noqa: E402
from dataset.sources import load_all  # noqa: E402

pools = load_all()
articles = []
for items in pools.values():
    for item in items:
        if item.get("article"):
            articles.append(item["article"])
print(f"pools={len(pools)} entries={len(articles)} unique={len(set(articles))}")
memo = crawl_pageviews(articles, workers=4)
ok = sum(1 for a in set(articles) if memo.get(a))
print(f"resolved={ok}/{len(set(articles))}")
