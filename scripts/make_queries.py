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
