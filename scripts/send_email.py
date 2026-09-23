"""Envoie le fichier Excel par e-mail via Gmail (SMTP).

Variables d'environnement (secrets GitHub) :
  GMAIL_USER          adresse Gmail qui envoie (ex. rachidleg77@gmail.com)
  GMAIL_APP_PASSWORD  mot de passe d'application Gmail (16 caracteres)
  MAIL_TO             destinataire
Usage : python scripts/send_email.py prospects.xlsx
"""
import os
import smtplib
import sys
from datetime import datetime
from email.message import EmailMessage


def main():
    fichier = sys.argv[1]
    user = os.environ["GMAIL_USER"]
    mdp = os.environ["GMAIL_APP_PASSWORD"].replace(" ", "")
    dest = os.environ.get("MAIL_TO") or user
    stats = open("stats.txt", encoding="utf-8").read().strip() if os.path.exists("stats.txt") else ""
    date = datetime.now().strftime("%d/%m/%Y")

    msg = EmailMessage()
    titre = os.environ.get("MAIL_TITRE", "").strip()
    msg["Subject"] = (f"[{titre}] " if titre else "") + f"Prospects cordiste fibrociment IDF - {stats.split('|')[0].strip()} - {date}"
    msg["From"] = user
    msg["To"] = dest
    msg.set_content(
        "Bonjour Rachid,\n\n"
        "Voici le fichier Excel des prospects (Paris + Ile-de-France) collectes sur Google Maps.\n\n"
        f"{stats}\n\n"
        "Onglets : 'Contacts avec e-mail', 'Sans e-mail (telephone)', 'Resume'.\n\n"
        "Rappel RGPD : prospection B2B uniquement, en lien avec l'activite du destinataire, "
        "avec un lien de desinscription dans chaque e-mail.\n"
    )
    with open(fichier, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=os.path.basename(fichier),
        )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, mdp)
        s.send_message(msg)
    print(f"E-mail envoye a {dest}")


if __name__ == "__main__":
    main()
