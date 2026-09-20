"""Fusionne les CSV du scraper, nettoie les e-mails et produit le fichier Excel.

Usage : python scripts/build_excel.py <dossier_csv> <sortie.xlsx>
Affiche le nombre d'e-mails trouves et l'ecrit dans stats.txt.
"""
import csv
import glob
import json
import os
import re
import sys
from collections import Counter

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

csv.field_size_limit(10**9)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
MAUVAIS_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js", ".ico")
MAUVAIS_DOMAINES = (
    "example.com", "example.fr", "exemple.fr", "exemple.com", "domain.com", "domaine.com",
    "email.com", "mail.com", "yourdomain", "votredomaine", "sentry", "wixpress.com",
    "godaddy.com", "mysite.com", "monsite.fr", "test.com", "company.com", "societe.com",
    "nom.fr", "adresse.fr",
)
MAUVAIS_DEBUTS = ("nom@", "name@", "prenom", "votre", "your", "email@", "user@", "xxx", "exemple@", "example@")


def email_valide(e: str) -> bool:
    e = e.lower()
    if len(e) > 80 or e.endswith(MAUVAIS_SUFFIXES) or "@2x" in e:
        return False
    if any(d in e.split("@", 1)[1] for d in MAUVAIS_DOMAINES):
        return False
    if e.startswith(MAUVAIS_DEBUTS):
        return False
    return True


def extraire_emails(champ: str):
    vus = []
    for e in EMAIL_RE.findall(champ or ""):
        e = e.strip(".").lower()
        if e.startswith("mailto:"):
            e = e[7:]
        if email_valide(e) and e not in vus:
            vus.append(e)
    return vus


def adresse_detaillee(brut: str):
    try:
        d = json.loads(brut) if brut else {}
        return d.get("postal_code", ""), d.get("city", "")
    except Exception:
        return "", ""


def lire_lignes(dossier):
    fichiers = sorted(glob.glob(os.path.join(dossier, "**", "*.csv"), recursive=True))
    for chemin in fichiers:
        with open(chemin, encoding="utf-8", errors="replace", newline="") as f:
            for row in csv.DictReader(f):
                yield row


def normaliser_tel(t):
    d = re.sub(r"\D", "", t or "")
    if d.startswith("33"):
        d = "0" + d[2:]
    return d if len(d) >= 9 else ""


def domaine(site):
    from urllib.parse import urlparse
    if not site:
        return ""
    d = urlparse(site if site.startswith("http") else "https://" + site).netloc.lower()
    d = d[4:] if d.startswith("www.") else d
    # les sites mutualises (pages facebook, annuaires...) ne permettent pas de regrouper
    if any(x in d for x in ("facebook.", "google.", "pagesjaunes", "linkedin", "instagram", "wixsite", "business.site")):
        return ""
    return d


def nom_norm(n):
    return re.sub(r"[^a-z0-9]", "", (n or "").lower())


class Groupes:
    """Regroupe les fiches d'une meme entreprise (meme site, telephone, e-mail ou nom+CP)."""

    def __init__(self):
        self.parent = {}

    def trouver(self, x):
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def unir(self, a, b):
        self.parent[self.trouver(a)] = self.trouver(b)


def main():
    dossier, sortie = sys.argv[1], sys.argv[2]
    fiches = []
    for row in lire_lignes(dossier):
        dep, metier, ville = (row.get("input_id", "") + "||").split("|")[:3]
        cp, commune = adresse_detaillee(row.get("complete_address", ""))
        fiches.append({
            "emails": extraire_emails(row.get("emails", "")),
            "source": row.get("source_email", "") or ("Google Maps" if row.get("emails") else ""),
            "Entreprise": row.get("title", ""),
            "Catégorie Google": row.get("category", ""),
            "Métier recherché": metier,
            "Département": dep,
            "Ville recherchée": ville,
            "Adresse": row.get("address", ""),
            "Code postal": cp,
            "Commune": commune,
            "Téléphone": row.get("phone", ""),
            "Site web": row.get("website", ""),
            "Note Google": row.get("review_rating", ""),
            "Nb avis": row.get("review_count", ""),
            "Fiche Google Maps": row.get("link", ""),
            "_place": row.get("place_id") or row.get("link") or "",
        })

    # 1) regroupement : une entreprise = meme fiche Maps, meme site, meme telephone, meme e-mail ou meme nom + code postal
    g = Groupes()
    for i, f in enumerate(fiches):
        cles = [f"i:{i}"]
        if f["_place"]:
            cles.append("p:" + f["_place"])
        if domaine(f["Site web"]):
            cles.append("d:" + domaine(f["Site web"]))
        if normaliser_tel(f["Téléphone"]):
            cles.append("t:" + normaliser_tel(f["Téléphone"]))
        if nom_norm(f["Entreprise"]) and (f["Code postal"] or f["Adresse"]):
            cles.append("n:" + nom_norm(f["Entreprise"]) + ":" + (f["Code postal"] or nom_norm(f["Adresse"])))
        cles += ["e:" + e for e in f["emails"]]
        for c in cles[1:]:
            g.unir(cles[0], c)

    entreprises = {}
    for i, f in enumerate(fiches):
        r = g.trouver(f"i:{i}")
        e = entreprises.setdefault(r, {"_emails": [], "_metiers": [], "_sources": [], **{k: v for k, v in f.items() if not k.startswith("_") and k not in ("emails", "source")}})
        for m in f["emails"]:
            if m not in e["_emails"]:
                e["_emails"].append(m)
        if f["Métier recherché"] and f["Métier recherché"] not in e["_metiers"]:
            e["_metiers"].append(f["Métier recherché"])
        if f["source"] and f["emails"] and f["source"] not in e["_sources"]:
            e["_sources"].append(f["source"])
        for k in ("Téléphone", "Site web", "Code postal", "Commune", "Adresse", "Catégorie Google"):
            if not e.get(k) and f.get(k):
                e[k] = f[k]

    contacts, sans_email = [], []
    for e in entreprises.values():
        e["Métier recherché"] = ", ".join(e["_metiers"])
        if e["_emails"]:
            e["E-mail"] = e["_emails"][0]
            e["Autres e-mails"] = "; ".join(e["_emails"][1:])
            e["Source de l'e-mail"] = ", ".join(e["_sources"])
            contacts.append(e)
        else:
            sans_email.append(e)
    places_vues = fiches
    contacts_emails = sum(len(c["_emails"]) for c in contacts)

    wb = Workbook()
    entete_style = Font(bold=True, color="FFFFFF")
    entete_fond = PatternFill("solid", fgColor="0B1B2B")

    def feuille(ws, lignes, colonnes):
        ws.append(colonnes)
        for c in ws[1]:
            c.font, c.fill = entete_style, entete_fond
            c.alignment = Alignment(vertical="center")
        for l in lignes:
            ws.append([l.get(col, "") for col in colonnes])
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        for i, col in enumerate(colonnes, 1):
            largeur = max([len(str(col))] + [len(str(l.get(col, ""))) for l in lignes[:2000]])
            ws.column_dimensions[get_column_letter(i)].width = min(max(10, largeur + 2), 60)

    cols = ["E-mail", "Autres e-mails", "Source de l'e-mail", "Entreprise", "Catégorie Google", "Métier recherché", "Département",
            "Ville recherchée", "Adresse", "Code postal", "Commune", "Téléphone", "Site web",
            "Note Google", "Nb avis", "Fiche Google Maps"]
    lignes = sorted(contacts, key=lambda l: (l["Département"], l["Métier recherché"], l["Entreprise"]))
    ws = wb.active
    ws.title = "Contacts avec e-mail"
    feuille(ws, lignes, cols)

    ws2 = wb.create_sheet("Sans e-mail (téléphone)")
    feuille(ws2, sorted(sans_email, key=lambda l: (l["Département"], l["Métier recherché"])), cols[3:])

    ws3 = wb.create_sheet("Résumé")
    ws3.append(["Entreprises avec e-mail (sans doublon)", len(contacts)])
    ws3.append(["Total adresses e-mail", contacts_emails])
    ws3.append(["Entreprises sans e-mail (avec téléphone/site)", len(sans_email)])
    ws3.append(["Fiches analysées (avant dédoublonnage)", len(places_vues)])
    ws3.append([])
    ws3.append(["E-mails par département", ""])
    for dep, n in sorted(Counter(l["Département"] for l in lignes).items()):
        ws3.append([dep, n])
    ws3.append([])
    ws3.append(["E-mails par métier", ""])
    for m, n in Counter(m for l in lignes for m in l["_metiers"]).most_common():
        ws3.append([m, n])
    ws3.column_dimensions["A"].width = 48
    for r in (1, 6):
        ws3.cell(row=r, column=1).font = Font(bold=True)

    wb.save(sortie)
    stats = f"{len(contacts)} entreprises avec e-mail ({contacts_emails} adresses) | {len(sans_email)} entreprises sans e-mail | {len(places_vues)} fiches analysees"
    with open("stats.txt", "w", encoding="utf-8") as f:
        f.write(stats + "\n")
    print(stats)


if __name__ == "__main__":
    main()
