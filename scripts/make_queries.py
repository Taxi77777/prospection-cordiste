"""Prepare les recherches Google Maps : Paris (20 arrondissements) + TOUTES les communes
des departements 77, 78, 91, 92, 93, 94, 95 (liste officielle geo.api.gouv.fr).

Le travail est decoupe en "lots" traites en parallele par GitHub Actions :
  - grandes villes (>= 15 000 habitants) et Paris : defilement complet (profondeur choisie) ;
  - petites communes : defilement court (les resultats y sont peu nombreux).

Usage :
  python scripts/make_queries.py plan '["75","77",...]' <profondeur>   -> matrice JSON des lots
  python scripts/make_queries.py lot <id_lot> queries.txt             -> requetes du lot
Chaque requete : "<metier> <commune> <dep>#!#<dep>|<metier>|<commune>"
"""
import json
import sys
import time
import urllib.request

from zones import METIERS, ZONES

SEUIL_GRANDE = 15000
TAILLE_LOT = {"g": 120, "p": 360}  # requetes par lot
PROFONDEUR_PETITES = 3


def communes(dep):
    """Liste (nom, population) triee par population decroissante."""
    if dep == "75":
        return [(v, 100000) for v in ZONES["75"]]
    url = f"https://geo.api.gouv.fr/departements/{dep}/communes?fields=nom,population"
    for essai in range(5):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                data = json.load(r)
            return sorted(((c["nom"], c.get("population") or 0) for c in data), key=lambda x: (-x[1], x[0]))
        except Exception:
            time.sleep(3 * (essai + 1))
    # secours : liste fixe des principales villes
    return [(v, SEUIL_GRANDE) for v in ZONES.get(dep, [])]


def requetes(dep, classe):
    lignes = []
    for ville, pop in communes(dep):
        grande = dep == "75" or pop >= SEUIL_GRANDE
        if (classe == "g") != grande:
            continue
        for metier in METIERS:
            texte = f"{metier} {ville}" + ("" if dep == "75" else f" {dep}")
            lignes.append(f"{texte}#!#{dep}|{metier}|{ville}")
    return lignes


def lots(dep, classe):
    lignes = requetes(dep, classe)
    n = TAILLE_LOT[classe]
    return [lignes[i:i + n] for i in range(0, len(lignes), n)]


def main():
    mode = sys.argv[1]
    if mode == "plan":
        deps = json.loads(sys.argv[2])
        prof = sys.argv[3] if len(sys.argv) > 3 else "15"
        import os
        os.makedirs("lots", exist_ok=True)
        matrice, total = [], 0
        for dep in deps:
            for classe in ("g", "p"):
                for i, lot in enumerate(lots(dep, classe)):
                    ident = f"{dep}-{classe}-{i}"
                    # les requetes de chaque lot sont figees ici (meme liste pour tous les jobs)
                    with open(f"lots/{ident}.txt", "w", encoding="utf-8") as f:
                        f.write("\n".join(lot) + "\n")
                    matrice.append({"id": ident,
                                    "profondeur": prof if classe == "g" else str(PROFONDEUR_PETITES)})
                    total += len(lot)
        print(json.dumps({"include": matrice}))
        print(f"{len(matrice)} lots, {total} requetes", file=sys.stderr)
    elif mode == "lot":
        dep, classe, i = sys.argv[2].split("-")
        lot = lots(dep, classe)[int(i)]
        with open(sys.argv[3], "w", encoding="utf-8") as f:
            f.write("\n".join(lot) + "\n")
        print(f"lot {sys.argv[2]} : {len(lot)} requetes")
    else:
        raise SystemExit("mode inconnu")


if __name__ == "__main__":
    main()
"""Genere le fichier de requetes Google Maps pour un departement.

Usage : python scripts/make_queries.py 92 queries.txt
Chaque ligne : "<metier> <ville>#!#<departement>|<metier>|<ville>"
(le texte apres #!# est repris tel quel dans la colonne input_id du resultat).
Les metiers prioritaires passent en premier, ville par ville.
"""
import sys
from zones import METIERS, ZONES


def main():
    dep, out = sys.argv[1], sys.argv[2]
    lignes = []
    for metier in METIERS:
        for ville in ZONES[dep]:
            lignes.append(f"{metier} {ville}#!#{dep}|{metier}|{ville}")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lignes) + "\n")
    print(f"{dep} : {len(lignes)} requetes -> {out}")


if __name__ == "__main__":
    main()
