"""Complete les e-mails manquants par d'autres canaux que Google Maps.

Pour chaque entreprise trouvee sans e-mail :
  1. son site web : page d'accueil + pages contact / mentions legales / a propos ;
  2. les moteurs de recherche (DuckDuckGo, Bing) : "<entreprise> <ville> email",
     e-mails visibles dans les resultats + pages contact des premiers sites trouves.

Usage : python scripts/enrich.py <dossier_csv_entree> <fichier_csv_sortie> [minutes_max]
Le CSV de sortie a les memes colonnes que celui du scraper (colonne "emails" completee).
"""
import csv
import glob
import os
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from html import unescape
from urllib.parse import quote_plus, urljoin, urlparse, parse_qs, unquote

import requests

csv.field_size_limit(10**9)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
OBF_RE = re.compile(r"([A-Za-z0-9._%+\-]+)\s*[\[\(]\s*(?:at|arobase|@)\s*[\]\)]\s*([A-Za-z0-9.\-]+)\s*[\[\(]\s*(?:dot|point|\.)\s*[\]\)]\s*([A-Za-z]{2,})", re.I)
MOTS_CONTACT = ("contact", "mentions", "legal", "a-propos", "apropos", "qui-sommes", "about", "coordonn", "agence", "nous-trouver")
IGNORES = ("facebook.com", "instagram.com", "linkedin.com", "twitter.com", "x.com", "youtube.com",
           "pagesjaunes.fr", "google.", "bing.com", "duckduckgo.com", "wikipedia.org", "societe.com",
           "pappers.fr", "verif.com", "infogreffe", "mappy.com", "tripadvisor", "yelp.")
UA = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0",
]


def get(url, timeout=12):
    try:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": random.choice(UA), "Accept-Language": "fr-FR,fr;q=0.9"})
        if r.status_code == 200 and "text/html" in r.headers.get("content-type", "text/html"):
            return r.text[:600_000]
    except Exception:
        pass
    return ""


def emails_dans(html):
    txt = unescape(html)
    found = set(e.lower().strip(".") for e in EMAIL_RE.findall(txt))
    for a, b, c in OBF_RE.findall(txt):
        found.add(f"{a}@{b}.{c}".lower())
    return {e for e in found if not e.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")) and "@2x" not in e}


def liens_contact(base, html):
    out = []
    for href in re.findall(r'href=["\']([^"\'#]+)', html, re.I):
        h = href.lower()
        if h.startswith("mailto:"):
            continue
        if any(m in h for m in MOTS_CONTACT):
            u = urljoin(base, href)
            if urlparse(u).netloc == urlparse(base).netloc and u not in out:
                out.append(u)
    return out[:4]


def fouiller_site(site):
    if not site:
        return set()
    if not site.startswith("http"):
        site = "https://" + site
    html = get(site)
    found = emails_dans(html)
    if found:
        return found
    for u in liens_contact(site, html) or [urljoin(site, p) for p in ("/contact", "/mentions-legales", "/nous-contacter")]:
        found |= emails_dans(get(u))
        if found:
            break
    return found


def recherche(q):
    """Resultats de moteurs de recherche : (e-mails vus dans les extraits, sites trouves)."""
    emails, sites = set(), []
    for url in (f"https://html.duckduckgo.com/html/?q={quote_plus(q)}",
                f"https://www.bing.com/search?q={quote_plus(q)}&setlang=fr&cc=FR"):
        html = get(url)
        if not html:
            continue
        emails |= emails_dans(html)
        for href in re.findall(r'href="([^"]+)"', html):
            if "duckduckgo.com/l/?" in href:
                href = unquote(parse_qs(urlparse(href).query).get("uddg", [""])[0])
            if href.startswith("http") and not any(i in href for i in IGNORES):
                dom = urlparse(href).scheme + "://" + urlparse(href).netloc
                if dom not in sites:
                    sites.append(dom)
        time.sleep(random.uniform(1.0, 2.5))
    return emails, sites[:2]


def domaine(site):
    d = urlparse(site if site.startswith("http") else "https://" + site).netloc.lower()
    return d[4:] if d.startswith("www.") else d


def cle_entreprise(row):
    """Site complet (domaine + chemin : chaque agence Foncia / Orpi... a sa propre page), sinon nom + adresse."""
    site = row.get("website", "")
    if site:
        return domaine(site) + urlparse(site if site.startswith("http") else "https://" + site).path.lower().rstrip("/")
    return (row.get("title", "") + row.get("address", "")).lower()


def completer(row):
    site = row.get("website", "")
    found = fouiller_site(site)
    source = "site web" if found else ""
    if not found:
        ville = (row.get("input_id", "||").split("|") + ["", "", ""])[2]
        q = f'"{row.get("title", "")}" {ville} email contact'
        vus, sites = recherche(q)
        # on ne garde les e-mails des moteurs que s'ils correspondent au site / nom de l'entreprise
        nom = re.sub(r"[^a-z0-9]", "", row.get("title", "").lower())[:8]
        dom = domaine(site) if site else ""
        for e in vus:
            d = e.split("@")[1]
            if (dom and d.endswith(dom)) or (nom and nom[:6] in re.sub(r"[^a-z0-9]", "", d)):
                found.add(e)
        if not found:
            for s in sites:
                if not dom or domaine(s) == dom or nom[:6] in domaine(s).replace("-", ""):
                    found |= fouiller_site(s)
                    if found:
                        break
        source = "moteur de recherche" if found else ""
    return found, source


def main():
    entree, sortie = sys.argv[1], sys.argv[2]
    minutes_max = float(sys.argv[3]) if len(sys.argv) > 3 else 60
    fin = time.time() + minutes_max * 60

    rows, champs = [], None
    for chemin in sorted(glob.glob(os.path.join(entree, "**", "*.csv"), recursive=True)):
        with open(chemin, encoding="utf-8", errors="replace", newline="") as f:
            r = csv.DictReader(f)
            if r.fieldnames and "emails" in r.fieldnames:
                champs = champs or r.fieldnames
                rows.extend(r)
    if not champs:
        print("aucun resultat")
        open(sortie, "w").close()
        return
    if "source_email" not in champs:
        champs = list(champs) + ["source_email"]

    # une seule tentative par entreprise (meme site / meme nom+adresse)
    a_faire, vus = {}, set()
    for i, row in enumerate(rows):
        row["source_email"] = "Google Maps" if EMAIL_RE.search(row.get("emails", "")) else ""
        if row["source_email"]:
            vus.add(cle_entreprise(row))
    for i, row in enumerate(rows):
        cle = cle_entreprise(row)
        if not row["source_email"] and cle not in vus and cle not in a_faire:
            a_faire[cle] = i
    print(f"{len(rows)} fiches, {len(a_faire)} entreprises sans e-mail a completer")

    trouves = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {}
        for cle, i in a_faire.items():
            futs[ex.submit(completer, rows[i])] = i
        for n, fut in enumerate(as_completed(futs), 1):
            i = futs[fut]
            try:
                found, source = fut.result()
            except Exception:
                found, source = set(), ""
            if found:
                rows[i]["emails"] = ", ".join(sorted(found))
                rows[i]["source_email"] = source
                trouves += 1
            if n % 100 == 0:
                print(f"  {n}/{len(futs)} traitees, {trouves} e-mails ajoutes")
            if time.time() > fin:
                print("duree max atteinte, arret de l'enrichissement")
                for f in futs:
                    f.cancel()
                break

    with open(sortie, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=champs, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"enrichissement termine : {trouves} entreprises completees -> {sortie}")


if __name__ == "__main__":
    main()
