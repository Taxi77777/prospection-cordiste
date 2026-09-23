"""Metiers cibles et zones geographiques (Paris + 7 departements d'Ile-de-France).

Modifier ces listes suffit pour changer la prospection : le workflow regenere
les requetes a chaque lancement.
"""

# Donneurs d'ordre (clients directs, pas de sous-traitance) susceptibles de commander
# des travaux de cordiste sur fibrociment.
# Classes par priorite : les premiers sont traites en premier dans chaque departement.
METIERS = [
    "syndic de copropriété",
    "bailleur social",
    "office HLM",
    "administrateur de biens",
    "gestion locative",
    "gestionnaire immobilier",
    "foncière immobilière",
    "agence immobilière",
    "architecte",
    "maître d'oeuvre bâtiment",
]

ZONES = {
    "75": [f"Paris {n}e" if n > 1 else "Paris 1er" for n in range(1, 21)],
    "77": ["Meaux", "Chelles", "Melun", "Pontault-Combault", "Savigny-le-Temple",
           "Bussy-Saint-Georges", "Champs-sur-Marne", "Torcy", "Serris", "Lagny-sur-Marne",
           "Villeparisis", "Roissy-en-Brie", "Le Mée-sur-Seine", "Combs-la-Ville", "Noisiel",
           "Fontainebleau", "Montereau-Fault-Yonne", "Provins", "Nemours", "Coulommiers"],
    "78": ["Versailles", "Saint-Germain-en-Laye", "Poissy", "Mantes-la-Jolie", "Sartrouville",
           "Montigny-le-Bretonneux", "Les Mureaux", "Plaisir", "Trappes", "Houilles",
           "Chatou", "Le Chesnay-Rocquencourt", "Élancourt", "Guyancourt", "Rambouillet",
           "Conflans-Sainte-Honorine", "Maisons-Laffitte", "Vélizy-Villacoublay", "Le Vésinet",
           "Chambourcy"],
    "91": ["Évry-Courcouronnes", "Corbeil-Essonnes", "Massy", "Savigny-sur-Orge",
           "Sainte-Geneviève-des-Bois", "Palaiseau", "Viry-Châtillon", "Athis-Mons", "Draveil",
           "Brunoy", "Yerres", "Grigny", "Les Ulis", "Étampes", "Juvisy-sur-Orge", "Longjumeau",
           "Montgeron", "Brétigny-sur-Orge", "Arpajon", "Orsay"],
    "92": ["Boulogne-Billancourt", "Nanterre", "Courbevoie", "Colombes", "Asnières-sur-Seine",
           "Rueil-Malmaison", "Issy-les-Moulineaux", "Levallois-Perret", "Neuilly-sur-Seine",
           "Antony", "Clichy", "Clamart", "Montrouge", "Suresnes", "Puteaux", "Gennevilliers",
           "Meudon", "Châtillon", "Bagneux", "Sèvres"],
    "93": ["Saint-Denis", "Montreuil", "Aubervilliers", "Aulnay-sous-Bois", "Drancy",
           "Noisy-le-Grand", "Pantin", "Bondy", "Épinay-sur-Seine", "Sevran", "Le Blanc-Mesnil",
           "Saint-Ouen-sur-Seine", "Bobigny", "Rosny-sous-Bois", "Livry-Gargan", "Villemomble",
           "Le Raincy", "Bagnolet", "Neuilly-sur-Marne", "Gagny"],
    "94": ["Créteil", "Vitry-sur-Seine", "Saint-Maur-des-Fossés", "Champigny-sur-Marne",
           "Ivry-sur-Seine", "Maisons-Alfort", "Fontenay-sous-Bois", "Villejuif", "Vincennes",
           "Choisy-le-Roi", "Nogent-sur-Marne", "Le Perreux-sur-Marne", "Charenton-le-Pont",
           "Alfortville", "Cachan", "L'Haÿ-les-Roses", "Thiais", "Orly",
           "Villeneuve-Saint-Georges", "Sucy-en-Brie"],
    "95": ["Argenteuil", "Cergy", "Sarcelles", "Garges-lès-Gonesse", "Franconville",
           "Goussainville", "Pontoise", "Bezons", "Ermont", "Villiers-le-Bel", "Gonesse",
           "Taverny", "Herblay-sur-Seine", "Sannois", "Eaubonne", "Cormeilles-en-Parisis",
           "Montmorency", "Saint-Ouen-l'Aumône", "Deuil-la-Barre", "Osny"],
}
