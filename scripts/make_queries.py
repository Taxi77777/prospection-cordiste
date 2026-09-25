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
    if dep in ("75", "77mlv"):
        return [(v, 100000) for v in ZONES[dep]]
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


def requetes(dep, classe, metiers=None):
    metiers = metiers or METIERS
    lignes = []
    dep_recherche = "77" if dep == "77mlv" else dep
    for ville, pop in communes(dep):
        grande = dep in ("75", "77mlv") or pop >= SEUIL_GRANDE
        if (classe == "g") != grande:
            continue
        for metier in metiers:
            texte = f"{metier} {ville}" + ("" if dep == "75" else f" {dep_recherche}")
            lignes.append(f"{texte}#!#{dep}|{metier}|{ville}")
    return lignes


def lots(dep, classe, metiers=None):
    lignes = requetes(dep, classe, metiers)
    n = TAILLE_LOT[classe]
    return [lignes[i:i + n] for i in range(0, len(lignes), n)]


def main():
    mode = sys.argv[1]
    if mode == "plan":
        deps = json.loads(sys.argv[2])
        prof = sys.argv[3] if len(sys.argv) > 3 else "15"
        # 4e argument optionnel : liste JSON de metiers pour ne chercher que ceux-la
        metiers = json.loads(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4].strip() else None
        # 5e argument optionnel : liste JSON de lots a refaire (ex. ["77-p-3","78-g-0"])
        seulement = set(json.loads(sys.argv[5])) if len(sys.argv) > 5 and sys.argv[5].strip() else None
        import os
        os.makedirs("lots", exist_ok=True)
        matrice, total = [], 0
        for dep in deps:
            for classe in ("g", "p"):
                for i, lot in enumerate(lots(dep, classe, metiers)):
                    ident = f"{dep}-{classe}-{i}"
                    if seulement and ident not in seulement:
                        continue
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
