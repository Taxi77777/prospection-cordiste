"""Envoie le mail type de la campagne assurance (taxi) en TEST sur MAIL_TO, flyer en piece jointe."""
import os
import smtplib
from email.message import EmailMessage

TEXTE = """Madame, Monsieur,

Lorsque l'un de vos assurés de Serris ou des environs a besoin d'un transport (retour au domicile après une hospitalisation, panne ou accident, rendez-vous médical, enfants à conduire à l'école), il faut souvent trouver un taxi fiable en urgence.

Taxi Marne-la-Vallée peut être ce partenaire local :
- plus de 30 chauffeurs, disponibles 24 h/24 et 7 j/7 ;
- les 41 communes de Marne-la-Vallée couvertes, ainsi que Paris, les gares et les aéroports ;
- berlines et vans jusqu'à 7 passagers ;
- facturation directe à l'assureur sur bon de prise en charge.

Vous trouverez notre plaquette en pièce jointe. Pouvons-nous être ajoutés à votre liste de prestataires taxi ? Il vous suffit de répondre à ce message ou de nous appeler au 07 50 53 56 58.

Cordialement,

Taxi Marne-la-Vallée
07 50 53 56 58 · contact@taximarnelavallee.com · taximarnelavallee.com

Vous ne souhaitez plus recevoir nos messages ? Se désinscrire
Taxi Marne-la-Vallée – SIREN 480 853 803 – 13 place Claude Monet, 77400 Saint-Thibault-des-Vignes."""

HTML = """<div style="max-width:600px;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.55;color:#1f2933;">
<p>Madame, Monsieur,</p>
<p>Lorsque l'un de vos assurés de Serris ou des environs a besoin d'un transport (retour au domicile après une hospitalisation, panne ou accident, rendez-vous médical, enfants à conduire à l'école), il faut souvent trouver un taxi fiable en urgence.</p>
<p>Taxi Marne-la-Vallée peut être ce partenaire local :</p>
<ul style="padding-left:20px;">
<li>plus de 30 chauffeurs, disponibles 24 h/24 et 7 j/7 ;</li>
<li>les 41 communes de Marne-la-Vallée couvertes, ainsi que Paris, les gares et les aéroports ;</li>
<li>berlines et vans jusqu'à 7 passagers ;</li>
<li>facturation directe à l'assureur sur bon de prise en charge.</li>
</ul>
<p>Vous trouverez notre plaquette en pièce jointe. Pouvons-nous être ajoutés à votre liste de prestataires taxi ? Il vous suffit de répondre à ce message ou de nous appeler au <a href="tel:+33750535658" style="color:#1f2933;">07 50 53 56 58</a>.</p>
<p>Cordialement,</p>
<p><strong>Taxi Marne-la-Vallée</strong><br>07 50 53 56 58 · <a href="mailto:contact@taximarnelavallee.com" style="color:#1f2933;">contact@taximarnelavallee.com</a> · <a href="https://taximarnelavallee.com" style="color:#1f2933;">taximarnelavallee.com</a></p>
<p style="font-size:11px;color:#7b8794;margin-top:28px;">Vous ne souhaitez plus recevoir nos messages ? <a href="#" style="color:#7b8794;">Se désinscrire</a><br>Taxi Marne-la-Vallée – SIREN 480 853 803 – 13 place Claude Monet, 77400 Saint-Thibault-des-Vignes.</p>
</div>"""


def main():
    user = os.environ["GMAIL_USER"]
    mdp = os.environ["GMAIL_APP_PASSWORD"].replace(" ", "")
    dest = os.environ.get("MAIL_TO") or user
    msg = EmailMessage()
    msg["Subject"] = "[TEST] Cabinet Exemple Assurances : un taxi partenaire pour vos garanties d'assistance à Marne-la-Vallée"
    msg["From"] = f"Taxi Marne-la-Vallée <{user}>"
    msg["To"] = dest
    msg["Reply-To"] = "contact@taximarnelavallee.com"
    msg.set_content(TEXTE)
    msg.add_alternative(HTML, subtype="html")
    with open("flyers/Flyer-Taxi-Assurances.pdf", "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename="Flyer-Taxi-Marne-la-Vallee.pdf")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(user, mdp)
        s.send_message(msg)
    print(f"Test envoye a {dest}")


if __name__ == "__main__":
    main()
