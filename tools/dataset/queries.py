"""Custom SPARQL for universes that need extra attributes."""

STATE_DETAIL_QUERY = """
SELECT ?item ?itemLabel ?sl ?article ?pop WHERE {
  {
    SELECT ?item (MAX(?pop_) AS ?pop) (MAX(?sl_) AS ?sl)
    WHERE {
      ?item wdt:P31/wdt:P279* wd:Q485258 .
      OPTIONAL { ?item wdt:P1082 ?pop_ . }
      OPTIONAL { ?item wikibase:sitelinks ?sl_ . }
    }
    GROUP BY ?item
  }
  OPTIONAL { ?article schema:about ?item ; schema:isPartOf <https://pt.wikipedia.org/> }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "pt,en". }
}
"""

PRESIDENTS_QUERY = """
SELECT ?item ?itemLabel ?sl ?article ?start WHERE {
  {
    SELECT ?item (MIN(?start_) AS ?start) (MAX(?sl_) AS ?sl)
    WHERE {
      ?item p:P39 ?st .
      ?st ps:P39 wd:Q5176750 .
      OPTIONAL { ?st pq:P580 ?start_ . }
      OPTIONAL { ?item wikibase:sitelinks ?sl_ . }
    }
    GROUP BY ?item
  }
  OPTIONAL { ?article schema:about ?item ; schema:isPartOf <https://pt.wikipedia.org/> }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "pt,en". }
}
"""

COUNTRY_QUERY = """
SELECT ?item ?itemLabel ?sl ?article ?contLabel WHERE {
  {
    SELECT ?item (MAX(?sl_) AS ?sl)
    WHERE {
      ?item wdt:P31 wd:Q6256 ; wdt:P297 ?iso .
      OPTIONAL { ?item wikibase:sitelinks ?sl_ . }
    }
    GROUP BY ?item
  }
  OPTIONAL { ?article schema:about ?item ; schema:isPartOf <https://pt.wikipedia.org/> }
  OPTIONAL { ?item wdt:P30 ?cont . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "pt,en". }
}
"""

WORLD_CAPITAL_QUERY = """
SELECT ?item ?itemLabel ?sl ?article ?contLabel WHERE {
  {
    SELECT ?item ?country (MAX(?sl_) AS ?sl)
    WHERE {
      ?country wdt:P31 wd:Q6256 ; wdt:P297 ?iso ; wdt:P36 ?item .
      OPTIONAL { ?item wikibase:sitelinks ?sl_ . }
    }
    GROUP BY ?item ?country
  }
  OPTIONAL { ?article schema:about ?item ; schema:isPartOf <https://pt.wikipedia.org/> }
  OPTIONAL { ?country wdt:P30 ?cont . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "pt,en". }
}
"""

ELEMENT_QUERY = """
SELECT ?item ?itemLabel ?sl ?article ?number WHERE {
  {
    SELECT ?item (MAX(?sl_) AS ?sl) (MAX(?n_) AS ?number)
    WHERE {
      ?item wdt:P31 wd:Q11344 ; wdt:P1086 ?n_ .
      OPTIONAL { ?item wikibase:sitelinks ?sl_ . }
    }
    GROUP BY ?item
  }
  OPTIONAL { ?article schema:about ?item ; schema:isPartOf <https://pt.wikipedia.org/> }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "pt,en". }
}
"""

WORLD_CITY_QUERY = """
SELECT ?item ?itemLabel ?sl ?article ?pop ?contLabel WHERE {
  {
    SELECT ?item (MAX(?pop_) AS ?pop) (MAX(?sl_) AS ?sl)
    WHERE {
      ?item wdt:P31 wd:Q515 ; wdt:P1082 ?pop_ .
      OPTIONAL { ?item wikibase:sitelinks ?sl_ . }
    }
    GROUP BY ?item
    ORDER BY DESC(?pop)
    LIMIT 240
  }
  OPTIONAL { ?article schema:about ?item ; schema:isPartOf <https://pt.wikipedia.org/> }
  OPTIONAL { ?item wdt:P17 ?country . ?country wdt:P30 ?cont . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "pt,en". }
}
"""
