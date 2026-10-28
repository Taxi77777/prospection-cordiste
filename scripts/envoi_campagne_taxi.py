"""Envoie le mail de prospection taxi (campagne assurance) a la liste CONTACTS (JSON [[email, entreprise, commune], ...]).
Expediteur : Gmail (GMAIL_USER) avec le nom "Taxi Marne-la-Vallee", reponses vers contact@taximarnelavallee.com.
Un mail toutes les 25-45 s, puis un rapport a MAIL_TO."""
import json
import os
import random
import smtplib
import time
from email.message import EmailMessage
from html import escape

REPONSE = "contact@taximarnelavallee.com"


def lieu(commune):
    return f"de {commune} ou des environs" if commune else "de Marne-la-Vallée"


def texte(c):
    return f"""Madame, Monsieur,

Lorsque l'un de vos assurés {lieu(c)} a besoin d'un transport (retour au domicile après une hospitalisation, panne ou accident, rendez-vous médical, enfants à conduire à l'école), il faut souvent trouver un taxi fiable en urgence.

Taxi Marne-la-Vallée peut être ce partenaire local :
- plus de 30 chauffeurs, disponibles 24 h/24 et 7 j/7 ;
- les 41 communes de Marne-la-Vallée couvertes, ainsi que Paris, les gares et les aéroports ;
- berlines et vans jusqu'à 7 passagers ;
- facturation directe à l'assureur sur bon de prise en charge.

Vous trouverez notre plaquette en pièce jointe. Pouvons-nous être ajoutés à votre liste de prestataires taxi ? Il vous suffit de répondre à ce message ou de nous appeler au 07 50 53 56 58.

Cordialement,

Taxi Marne-la-Vallée
07 50 53 56 58 · contact@taximarnelavallee.com · taximarnelavallee.com

Vous ne souhaitez plus recevoir nos messages ? Répondez simplement STOP."""


def html(c):
    return f"""<div style="max-width:600px;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.55;color:#1f2933;">
<p>Madame, Monsieur,</p>
<p>Lorsque l'un de vos assurés {escape(lieu(c))} a besoin d'un transport (retour au domicile après une hospitalisation, panne ou accident, rendez-vous médical, enfants à conduire à l'école), il faut souvent trouver un taxi fiable en urgence.</p>
<p>Taxi Marne-la-Vallée peut être ce partenaire local :</p>
<ul style="padding-left:20px;">
<li>plus de 30 chauffeurs, disponibles 24 h/24 et 7 j/7 ;</li>
<li>les 41 communes de Marne-la-Vallée couvertes, ainsi que Paris, les gares et les aéroports ;</li>
<li>berlines et vans jusqu'à 7 passagers ;</li>
<li>facturation directe à l'assureur sur bon de prise en charge.</li>
</ul>
<p>Vous trouverez notre plaquette en pièce jointe. Pouvons-nous être ajoutés à votre liste de prestataires taxi ? Il vous suffit de répondre à ce message ou de nous appeler au <a href="tel:+33750535658" style="color:#1f2933;">07 50 53 56 58</a>.</p>
<p>Cordialement,</p>
<p><strong>Taxi Marne-la-Vallée</strong><br>07 50 53 56 58 · <a href="mailto:{REPONSE}" style="color:#1f2933;">{REPONSE}</a> · <a href="https://taximarnelavallee.com" style="color:#1f2933;">taximarnelavallee.com</a></p>
<p style="font-size:11px;color:#7b8794;margin-top:28px;">Vous ne souhaitez plus recevoir nos messages ? Répondez simplement STOP.</p>
</div>"""


def sujet(nom):
    base = "un taxi partenaire pour vos garanties d'assistance à Marne-la-Vallée"
    return f"{nom.strip()} : {base}" if nom and len(nom) <= 50 else base[0].upper() + base[1:]


def main():
    contacts = json.loads(os.environ["CONTACTS"])
    user = os.environ["GMAIL_USER"]
    mdp = os.environ["GMAIL_APP_PASSWORD"].replace(" ", "")
    rapport_to = os.environ.get("MAIL_TO") or user
    flyer = open("flyers/Flyer-Taxi-Assurances.pdf", "rb").read()
    ok, ko = [], []
    s = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    s.login(user, mdp)
    for i, (email, nom, commune) in enumerate(contacts):
        c = (commune or "").strip()
        msg = EmailMessage()
        msg["Subject"] = sujet(nom)
        msg["From"] = f"Taxi Marne-la-Vallée <{user}>"
        msg["To"] = email
        msg["Reply-To"] = REPONSE
        msg["List-Unsubscribe"] = f"<mailto:{REPONSE}?subject=STOP>"
        msg.set_content(texte(c))
        msg.add_alternative(html(c), subtype="html")
        msg.add_attachment(flyer, maintype="application", subtype="pdf", filename="Flyer-Taxi-Marne-la-Vallee.pdf")
        try:
            try:
                s.send_message(msg)
            except smtplib.SMTPServerDisconnected:
                s = smtplib.SMTP_SSL("smtp.gmail.com", 465)
                s.login(user, mdp)
                s.send_message(msg)
            ok.append(email)
            print(f"{i + 1}/{len(contacts)} envoye")
        except Exception as e:
            ko.append(f"{email} : {e}")
            print(f"{i + 1}/{len(contacts)} ERREUR {e}")
        if i < len(contacts) - 1:
            time.sleep(random.uniform(25, 45))
    r = EmailMessage()
    r["Subject"] = f"Rapport envoi taxi assurances : {len(ok)} mails envoyes, {len(ko)} erreurs"
    r["From"] = user
    r["To"] = rapport_to
    r.set_content(f"Envoyes : {len(ok)}\nErreurs : {len(ko)}\n\n" + "\n".join(ko) +
                  "\n\nLes reponses arrivent sur contact@taximarnelavallee.com. Les retours 'STOP' sont a ne plus contacter.")
    s.send_message(r)
    s.quit()
    print(f"Termine : {len(ok)} envoyes, {len(ko)} erreurs")


if __name__ == "__main__":
    main()
