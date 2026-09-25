"""Complete Google Maps par l'annuaire officiel des entreprises francaises (INSEE/Sirene, data.gouv.fr).

Ratisse large : TOUTES les entreprises actives des communes des zones "restreintes" de zones.py
(ex. 77mlv), sauf une petite liste d'activites grand public sans interet pour la prospection B2B
(fast-food/restauration, salles de sport/loisirs, coiffure) -> voir EXCLURE_PREFIXES.
Jamais un departement entier (voir ZONES_RESTREINTES). Source officielle et gratuite, sans risque
de blocage anti-robot (contrairement a un site comme PagesJaunes qui bloque tres vite les robots).
Ne fournit pas d'e-mail ni de site web : les lignes produites ont le meme format que celles du
scraper Google Maps, sans e-mail, pour que scripts/enrich.py cherche l'e-mail (site + moteurs de
recherche) exactement comme pour les fiches Google Maps sans e-mail.

Usage : python scripts/annuaire_gouv.py <departements_json> <dossier_sortie>
"""
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from zones import ZONES

# Zones "restreintes" (liste fixe de communes, pas tout un departement) : seules celles-la sont
# traitees ici, pour ne jamais elargir a un departement entier par erreur.
ZONES_RESTREINTES = ("75", "77mlv")

# Activites grand public sans interet pour un client B2B (taxi/transfert professionnel) :
# prefixes de code NAF/APE a exclure des resultats.
EXCLURE_PREFIXES = (
    "56.",    # restauration et debits de boissons (fast-food, restaurants, bars, cafes)
    "93.1",   # activites sportives (salles de sport, clubs)
    "93.2",   # autres activites recreatives et de loisirs
    "96.02",  # coiffure et soins de beaute
)

GEO_API = "https://geo.api.gouv.fr/communes"
RECHERCHE_API = "https://recherche-entreprises.api.gouv.fr/search"
PAGES_MAX = 40  # ratisse large : jusqu'a 1000 entreprises actives par commune


def get_json(url, essais=3):
    for i in range(essais):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "prospection-77mlv/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429 and i < essais - 1:
                time.sleep(5 * (i + 1))
                continue
            return None
        except Exception:
            if i < essais - 1:
                time.sleep(2 * (i + 1))
                continue
            return None
    return None


def code_insee(nom_commune, dep):
    prefixe = "75" if dep == "75" else "77"
    q = urllib.parse.urlencode({"nom": nom_commune, "fields": "nom,code", "boost": "population"})
    data = get_json(f"{GEO_API}?{q}") or []
    for c in data:
        if c.get("code", "").startswith(prefixe):
            return c["code"]
    return data[0]["code"] if data else None


def entreprises(code_commune):
    lignes, page = [], 1
    while page <= PAGES_MAX:
        q = urllib.parse.urlencode({
            "code_commune": code_commune,
            "etat_administratif": "A",
            "page": page,
            "per_page": 25,
        })
        data = get_json(f"{RECHERCHE_API}?{q}")
        time.sleep(0.12)
        if not data or not data.get("results"):
            break
        lignes.extend(data["results"])
        if len(data["results"]) < 25:
            break
        page += 1
    return lignes


def exclue(res):
    code = res.get("activite_principale") or ""
    return any(code.startswith(p) for p in EXCLURE_PREFIXES)


def ligne_csv(res, dep, ville):
    siege = res.get("siege") or {}
    siren = res.get("siren", "")
    return {
        "title": res.get("nom_complet") or res.get("nom_raison_sociale") or "",
        "category": f"Annuaire entreprises : {res.get('activite_principale', '')}",
        "address": siege.get("adresse", ""),
        "complete_address": json.dumps({"postal_code": siege.get("code_postal", ""), "city": siege.get("libelle_commune", "")}),
        "phone": "",
        "website": "",
        "review_rating": "",
        "review_count": "",
        "link": f"https://annuaire-entreprises.data.gouv.fr/entreprise/{siren}" if siren else "",
        "emails": "",
        "cid": "",
        "data_id": "",
        "place_id": "",
        "input_id": f"{dep}|Annuaire entreprises|{ville}",
    }


def main():
    deps = json.loads(sys.argv[1])
    dossier = sys.argv[2]
    lignes, vus = [], set()
    for dep in deps:
        if dep not in ZONES_RESTREINTES:
            continue
        for ville in ZONES[dep]:
            code = code_insee(ville, dep)
            if not code:
                print(f"  code INSEE introuvable pour {ville}")
                continue
            for res in entreprises(code):
                siren = res.get("siren")
                if not siren or siren in vus:
                    continue
                if res.get("etat_administratif") != "A":
                    continue
                if exclue(res):
                    continue
                vus.add(siren)
                lignes.append(ligne_csv(res, dep, ville))
            print(f"  {ville} : {len(vus)} entreprises cumulees")
    print(f"{len(lignes)} entreprises trouvees via l'annuaire officiel (data.gouv.fr)")
    champs = ["title", "category", "address", "complete_address", "phone", "website",
              "review_rating", "review_count", "link", "emails", "cid", "data_id", "place_id", "input_id"]
    os.makedirs(dossier, exist_ok=True)
    with open(f"{dossier}/resultats-annuairegouv.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs)
        w.writeheader()
        w.writerows(lignes)


if __name__ == "__main__":
    main()
