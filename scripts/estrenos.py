#!/usr/bin/env python3
"""Genera estrenos.json: títulos nuevos este mes en plataformas de streaming en España (datos de JustWatch)."""
import datetime as dt, json, time, urllib.request

PLATAFORMAS = [("nfx","Netflix"),("prv","Prime Video"),("dnp","Disney+"),("fil","Filmin"),("mxx","HBO Max"),("atp","Apple TV+")]
Q = """query N($country: Country!, $date: Date!, $language: Language!, $filter: TitleFilter, $first: Int!) {
 newTitles(country: $country, date: $date, filter: $filter, first: $first, priceDrops: false, pageType: NEW) {
  edges { node { ... on MovieOrShow { objectType content(country: $country, language: $language) { title originalReleaseYear posterUrl fullPath } }
                 ... on Season { objectType show { content(country: $country, language: $language) { title originalReleaseYear posterUrl fullPath } } } } } } }"""

def ask(pkg, day):
    body = {"query": Q, "variables": {"country":"ES","language":"es","first":40,"date":day,
            "filter":{"packages":[pkg],"objectTypes":["MOVIE","SHOW"]}}}
    req = urllib.request.Request("https://apis.justwatch.com/graphql", json.dumps(body).encode(),
                                 {"Content-Type":"application/json","User-Agent":"panel-estrenos/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["data"]["newTitles"]["edges"]

hoy = dt.date.today()
out = {"actualizado": dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%MZ"), "mes": hoy.strftime("%Y-%m"), "plataformas": []}
for code, name in PLATAFORMAS:
    vistos, items = set(), []
    d = hoy
    while d.month == hoy.month:
        try:
            for e in ask(code, d.isoformat()):
                n = e["node"]; c = n.get("content") or (n.get("show") or {}).get("content") or {}
                t = c.get("title")
                if not t or t in vistos: continue
                vistos.add(t)
                p = c.get("posterUrl") or ""
                items.append({"t": t, "y": c.get("originalReleaseYear"), "tipo": "Película" if n.get("objectType")=="MOVIE" else "Serie",
                              "f": d.isoformat(), "img": ("https://images.justwatch.com"+p.replace("{profile}","s166").replace("{format}","jpg")) if p else "",
                              "url": "https://www.justwatch.com"+(c.get("fullPath") or "")})
        except Exception as ex:
            print(code, d, "error", ex)
        time.sleep(0.3)
        d -= dt.timedelta(days=1)
    out["plataformas"].append({"id": code, "nombre": name, "titulos": items[:40]})
    print(name, len(items))
json.dump(out, open("estrenos.json","w",encoding="utf-8"), ensure_ascii=False, indent=0)
