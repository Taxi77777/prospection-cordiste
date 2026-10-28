"""2e passe : cherche l'e-mail des assureurs restes sans e-mail (liste JSON SANS : [[nom, commune, site, tel], ...]).
Plus profond que enrich.py : plusieurs formulations de recherche, 5 sites candidats, exploration de 10 pages par site.
Ecrit un Excel et l'envoie par Gmail a MAIL_TO."""
import json
import os
import re
import smtplib
import sys
import time
import random
from concurrent.futures import ThreadPoolExecutor
from email.message import EmailMessage
from urllib.parse import urljoin, urlparse

sys.path.insert(0, os.path.dirname(__file__))
from enrich import IGNORES, domaine, emails_dans, get, recherche_brute  # noqa: E402
from openpyxl import Workbook

ROLE = re.compile(r"^(dpo|webmaster|noreply|no-reply|rgpd|privacy|donnees|test|admin|postmaster|abuse|recrutement|rh|jobs|careers|candidature|reclamation)[@.]")
MOTS = ("contact", "mentions", "legal", "propos", "equipe", "agence", "nous", "coordonn", "cabinet", "qui-sommes")
EXCLURE = re.compile(r"expertise auto|expert auto", re.I)


def jetons(nom):
    mots = re.findall(r"[a-z0-9]{3,}", nom.lower())
    return [m for m in mots if m not in ("assurance", "assurances", "courtage", "conseil", "conseils", "patrimoine", "cabinet", "agence", "groupe", "france", "les", "des", "sas", "sarl", "eurl")]


def explorer(site, n=10):
    if not site.startswith("http"):
        site = "https://" + site
    html = get(site)
    found = emails_dans(html)
    vus, liens = {site}, []
    for href in re.findall(r'href=["\']([^"\'#]+)', html, re.I):
        u = urljoin(site, href)
        if urlparse(u).netloc == urlparse(site).netloc and any(m in u.lower() for m in MOTS) and u not in vus:
            vus.add(u)
            liens.append(u)
    for u in (liens + [urljoin(site, p) for p in ("/contact", "/mentions-legales", "/nous-contacter", "/contactez-nous")])[:n]:
        found |= emails_dans(get(u))
    return found


def propres(emails, nom, dom=""):
    j = jetons(nom)
    out = set()
    for e in emails:
        if ROLE.match(e) or len(e) > 70:
            continue
        d = e.split("@")[1]
        if (dom and d.endswith(dom)) or any(t in d.replace("-", "") or t in e.split("@")[0] for t in j):
            out.add(e)
    return out


def traiter(item):
    nom, commune, site, tel = item
    if EXCLURE.search(nom):
        return None
    trouves, source = set(), ""
    if site:
        trouves = propres(explorer(site), nom, domaine(site)) or {e for e in explorer(site) if not ROLE.match(e)}
        source = "site web" if trouves else ""
    if not trouves:
        j = jetons(nom)
        for q in (f'"{nom}" {commune} assurance', f'{nom} {commune} courtier assurance email', f'"{nom}" contact'):
            vus, sites = recherche_brute(q, 5)
            trouves |= propres(vus, nom)
            for s in sites:
                d = domaine(s).replace("-", "")
                if j and any(t in d for t in j):
                    trouves |= propres(explorer(s, 6), nom, domaine(s))
                    if trouves:
                        site = site or s
                        break
            if trouves:
                source = "moteur de recherche"
                break
            time.sleep(random.uniform(1, 2))
    return [nom, commune, ", ".join(sorted(trouves)), source, site, tel]


def main():
    items = json.loads(os.environ["SANS"])
    with ThreadPoolExecutor(max_workers=6) as ex:
        res = [r for r in ex.map(traiter, items) if r]
    avec = [r for r in res if r[2]]
    wb = Workbook()
    ws = wb.active
    ws.title = "Nouveaux e-mails"
    ws.append(["Entreprise", "Commune", "E-mail(s)", "Source", "Site", "Téléphone"])
    for r in avec:
        ws.append(r)
    ws2 = wb.create_sheet("Toujours sans e-mail")
    ws2.append(["Entreprise", "Commune", "Site", "Téléphone"])
    for r in res:
        if not r[2]:
            ws2.append([r[0], r[1], r[4], r[5]])
    f = "assureurs-41-communes-2e-passe.xlsx"
    wb.save(f)
    print(f"{len(avec)} nouveaux e-mails sur {len(res)} assureurs")
    user = os.environ["GMAIL_USER"]
    msg = EmailMessage()
    msg["Subject"] = f"2e passe assureurs 41 communes : {len(avec)} nouveaux e-mails trouves sur {len(res)}"
    msg["From"] = user
    msg["To"] = os.environ.get("MAIL_TO") or user
    msg.set_content(f"{len(avec)} assureurs des 41 communes ont maintenant un e-mail (onglet 'Nouveaux e-mails').\nAucun mail n'a ete envoye a ces contacts.")
    msg.add_attachment(open(f, "rb").read(), maintype="application", subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=f)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, os.environ["GMAIL_APP_PASSWORD"].replace(" ", ""))
        s.send_message(msg)


if __name__ == "__main__":
    main()
