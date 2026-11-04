import sys

sys.path.insert(0, "tools")
from dataset.http import sparql  # noqa: E402

Q = """
SELECT ?item ?itemLabel ?sl ?contLabel WHERE {
  {
    SELECT ?item ?country (MAX(?sl_) AS ?sl) WHERE {
      ?country wdt:P31 wd:Q6256 ; wdt:P297 ?iso ; wdt:P36 ?item .
      OPTIONAL { ?item wikibase:sitelinks ?sl_ . }
    } GROUP BY ?item ?country
  }
  OPTIONAL { ?country wdt:P30 ?cont }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "pt,en". }
}
"""

rows = sparql(Q)
print("count", len(rows))
labels = [r.get("itemLabel", "?") for r in rows]
print("first 15:", labels[:15])
print("tokyo?", [label for label in labels if "Tóquio" in label or "Toquio" in label])
print("continents:", {r.get("contLabel", "?") for r in rows})
