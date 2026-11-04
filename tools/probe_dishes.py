import sys

sys.path.insert(0, "tools")
from dataset.http import sparql  # noqa: E402

DISHES = """
SELECT ?item ?itemLabel ?sl WHERE {
  {
    SELECT ?item (MAX(?sl_) AS ?sl) WHERE {
      ?item wdt:P31/wdt:P279* wd:Q746549 .
      OPTIONAL { ?item wikibase:sitelinks ?sl_ . }
    } GROUP BY ?item ORDER BY DESC(?sl) LIMIT 400
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "pt,en". }
}
"""

rows = sparql(DISHES)
labels = [r.get("itemLabel", "?") for r in rows]
print("dishes", len(labels))
print("first 20:", labels[:20])
print("strog?", [x for x in labels if "strog" in x.lower() or "estrog" in x.lower()])
