"""Fictitious demo content. Every person and company here is invented (emails use example.com)."""

# (slug, emoji, category, label_fr, label_de, label_en, icebreaker_fr, icebreaker_de, icebreaker_en)
TAGS = [
    ("ski-rando", "⛷️", "hobby", "Ski de randonnée", "Skitouren", "Ski touring",
     "Demande-lui sa plus belle course de l'hiver dernier.", "Frag nach der schönsten Tour des letzten Winters.", "Ask about the best tour of last winter."),
    ("patrouille-glaciers", "🏔️", "hobby", "Patrouille des Glaciers", "Patrouille des Glaciers", "Patrouille des Glaciers",
     "La Patrouille : souvenir mémorable ou projet secret ?", "Die Patrouille: unvergessliche Erinnerung oder geheimes Projekt?", "The Patrouille: unforgettable memory or secret plan?"),
    ("vtt", "🚵", "hobby", "VTT", "Mountainbike", "Mountain biking",
     "Échangez vos meilleurs sentiers en Valais.", "Tauscht eure besten Trails im Wallis aus.", "Swap your favourite trails in Valais."),
    ("golf", "⛳", "hobby", "Golf", "Golf", "Golf",
     "Quel parcours valaisan mérite le détour ?", "Welcher Walliser Golfplatz lohnt sich am meisten?", "Which Valais course is worth the trip?"),
    ("trail", "🏃", "hobby", "Course à pied & trail", "Laufen & Trailrunning", "Running & trail",
     "Quelle est la prochaine course au programme ?", "Welcher Lauf steht als Nächstes auf dem Programm?", "What's the next race on the calendar?"),
    ("peche-chasse", "🎣", "hobby", "Pêche & chasse", "Fischen & Jagen", "Fishing & hunting",
     "Demande-lui son meilleur coin… sans espoir qu'on te le révèle.", "Frag nach dem besten Platz – verraten wird er sicher nicht.", "Ask for their best spot – don't expect an answer."),
    ("cols-moto", "🏍️", "hobby", "Moto & cols alpins", "Motorrad & Alpenpässe", "Motorbikes & alpine passes",
     "Grimsel, Furka ou Simplon : quel col en premier ?", "Grimsel, Furka oder Simplon: welcher Pass zuerst?", "Grimsel, Furka or Simplon: which pass first?"),
    ("cuisine", "🍳", "hobby", "Cuisine", "Kochen", "Cooking",
     "Quelle est sa recette signature ?", "Was ist das Lieblingsrezept?", "What's the signature dish?"),
    ("raclette", "🧀", "valais", "Raclette au feu de bois", "Raclette am Holzfeuer", "Wood-fire raclette",
     "Ouvrez le débat : quel fromage d'alpage fait la meilleure raclette ?", "Eröffnet die Debatte: Welcher Alpkäse ergibt die beste Raclette?", "Open the debate: which alpine cheese makes the best raclette?"),
    ("fendant", "🥂", "valais", "Fendant", "Fendant", "Fendant",
     "Quelle cave pour un Fendant à l'apéro ?", "Welcher Keller für einen Fendant zum Apéro?", "Which cellar for a Fendant at apéro time?"),
    ("petite-arvine", "🍾", "valais", "Petite Arvine", "Petite Arvine", "Petite Arvine",
     "Petite Arvine sèche ou flétrie ? Débat garanti.", "Petite Arvine trocken oder süss? Diskussion garantiert.", "Petite Arvine dry or late-harvest? Debate guaranteed."),
    ("cornalin", "🍷", "valais", "Cornalin & Humagne", "Cornalin & Humagne", "Cornalin & Humagne",
     "Le meilleur millésime goûté jusqu'ici ?", "Der beste Jahrgang bisher?", "Best vintage tasted so far?"),
    ("combats-reines", "🐄", "valais", "Combats de reines", "Ringkuhkämpfe", "Hérens cow fights",
     "Une reine a-t-elle déjà fait partie de la famille ?", "Gab es schon einmal eine Königin in der Familie?", "Has a queen cow ever been part of the family?"),
    ("fc-sion", "⚽", "valais", "FC Sion", "FC Sion", "FC Sion",
     "Parlez du dernier match… à vos risques et périls.", "Sprecht über das letzte Spiel – auf eigene Gefahr.", "Talk about the last match – at your own risk."),
    ("hockey", "🏒", "valais", "Hockey sur glace", "Eishockey", "Ice hockey",
     "Sierre ou Viège ? Choisis bien ton camp.", "Siders oder Visp? Wähle dein Lager mit Bedacht.", "Sierre or Visp? Choose your side wisely."),
    ("carnaval", "🎭", "valais", "Carnaval", "Fasnacht", "Carnival",
     "Quel a été le pire (ou le meilleur) déguisement ?", "Was war das schlimmste (oder beste) Kostüm?", "Worst (or best) costume ever?"),
    ("abricots", "🍑", "valais", "Abricots du Valais", "Walliser Aprikosen", "Valais apricots",
     "Abricotine ou confiture ? Question sérieuse.", "Abricotine oder Konfitüre? Eine ernste Frage.", "Abricotine or jam? A serious question."),
    ("foire", "🎪", "valais", "La Foire du Valais", "Die Foire du Valais", "The Foire du Valais",
     "Son meilleur souvenir de Foire ?", "Die schönste Erinnerung an die Foire?", "Best Foire memory?"),
    ("musique-classique", "🎻", "culture", "Musique classique", "Klassische Musik", "Classical music",
     "Le plus beau concert de l'année ?", "Das schönste Konzert des Jahres?", "Best concert of the year?"),
    ("festivals", "🎸", "culture", "Festivals & concerts", "Festivals & Konzerte", "Festivals & gigs",
     "Quel festival ne se rate sous aucun prétexte ?", "Welches Festival darf man auf keinen Fall verpassen?", "Which festival is never to be missed?"),
    ("lecture", "📚", "culture", "Lecture", "Lesen", "Reading",
     "Le dernier livre vraiment marquant ?", "Das letzte Buch, das wirklich beeindruckt hat?", "Last book that really stuck?"),
    ("voyages", "✈️", "culture", "Voyages lointains", "Fernreisen", "Far-away travel",
     "La prochaine destination ?", "Das nächste Reiseziel?", "Next destination?"),
    ("ia", "🤖", "culture", "Intelligence artificielle", "Künstliche Intelligenz", "Artificial intelligence",
     "Qu'est-ce que l'IA a déjà changé dans son entreprise ?", "Was hat KI im eigenen Unternehmen schon verändert?", "What has AI already changed in their company?"),
    ("reunions-lundi", "📅", "work", "Les réunions du lundi matin", "Montagmorgen-Meetings", "Monday morning meetings",
     "Partagez vos meilleures techniques pour les éviter.", "Teilt eure besten Tricks, um sie zu vermeiden.", "Share your best tricks to avoid them."),
    ("emails-nuit", "🌙", "work", "Les e-mails à 23 h", "E-Mails um 23 Uhr", "Emails at 11 pm",
     "Comparez vos règles pour protéger vos soirées.", "Vergleicht eure Regeln, um die Abende zu schützen.", "Compare your rules for protecting your evenings."),
    ("bouchons-a9", "🚗", "work", "Les bouchons sur l'A9", "Stau auf der A9", "Traffic jams on the A9",
     "Échangez vos itinéraires secrets.", "Tauscht eure geheimen Schleichwege aus.", "Swap your secret shortcuts."),
    ("powerpoint", "📊", "work", "Les présentations PowerPoint", "PowerPoint-Präsentationen", "PowerPoint decks",
     "Le pire slide jamais vu ?", "Die schlimmste Folie aller Zeiten?", "Worst slide ever seen?"),
    ("networking-force", "🤝", "work", "Le networking forcé", "Erzwungenes Networking", "Forced networking",
     "Bonne nouvelle : ici, c'est un apéro, pas un pitch.", "Gute Nachricht: Hier ist Apéro, kein Pitch.", "Good news: this is an apéro, not a pitch."),
    ("teletravail", "🏠", "work", "Le télétravail", "Homeoffice", "Remote work",
     "Bureau, maison ou chalet ?", "Büro, Zuhause oder Chalet?", "Office, home or chalet?"),
    ("open-space", "🏢", "work", "Les open spaces", "Grossraumbüros", "Open-plan offices",
     "Pour ou contre ? Défendez votre camp.", "Dafür oder dagegen? Verteidigt eure Seite.", "For or against? Defend your side."),
]

STAFF = {"email": "equipe@example.com", "first_name": "Équipe", "last_name": "Événements"}

# Demo storyline: Camille (newcomer) must be introduced to Lukas (pillar) at the upcoming dinner.
CAMILLE = {
    "email": "camille.rey@example.com", "first_name": "Camille", "last_name": "Rey",
    "company": "Bisse Digital Sàrl", "job_title": "Fondatrice & CEO", "sector": "tech", "region": "Martigny",
    "speaks_fr": True, "speaks_de": False, "speaks_en": True, "member_since": None,  # None = current year
    "fun_fact": "A traversé la Haute Route Chamonix–Zermatt en six jours.",
    "talk_to_me_about": "La transformation digitale des PME", "phone": "+41 79 000 00 01",
    "likes": ["ski-rando", "petite-arvine", "trail", "ia", "festivals"], "dislikes": ["reunions-lundi", "bouchons-a9"],
}
LUKAS = {
    "email": "lukas.imboden@example.com", "first_name": "Lukas", "last_name": "Imboden",
    "company": "Lärchenwerk AG", "job_title": "Geschäftsführer", "sector": "construction", "region": "Brig",
    "speaks_fr": True, "speaks_de": True, "speaks_en": False, "member_since": 2017,
    "fun_fact": "A terminé douze fois la Patrouille des Glaciers.",
    "talk_to_me_about": "La construction bois en montagne", "phone": "+41 79 000 00 02",
    "likes": ["ski-rando", "petite-arvine", "trail", "patrouille-glaciers", "combats-reines"],
    "dislikes": ["reunions-lundi", "powerpoint"],
    "qr_token": "demo-lukas",  # fixed on purpose: the README links to /m/demo-lukas/ to replay the meeting on stage
}

FIRST_NAMES_FR = [
    "Julien", "Sophie", "Nicolas", "Valérie", "Pierre-Alain", "Nathalie", "Grégoire", "Isabelle", "Yannick",
    "Stéphanie", "Christophe", "Mélanie", "Raphaël", "Céline", "Didier", "Sandrine", "Olivier", "Aline",
    "Fabrice", "Laurence", "Sébastien", "Delphine", "Jérôme", "Florence", "Patrick", "Joëlle", "Alexandre",
    "Mathilde", "Vincent", "Caroline", "Frédéric", "Sarah",
]
LAST_NAMES_FR = [
    "Fournier", "Michellod", "Bonvin", "Carron", "Moret", "Gay", "Pralong", "Crettenand", "Vouilloz",
    "Zufferey", "Salamin", "Theytaz", "Favre", "Délèze", "Fellay", "Luisier", "Rossier", "Bruchez",
    "Gaillard", "Darbellay", "Dorsaz", "Mayor", "Pitteloud", "Roduit",
]
FIRST_NAMES_DE = ["Stefan", "Andrea", "Thomas", "Sandra", "Daniel", "Nicole", "Reto", "Corinne", "Beat", "Manuela", "Urs", "Simone", "Martin", "Claudia"]
LAST_NAMES_DE = ["Imhof", "Zenklusen", "Kalbermatten", "Schmid", "Bumann", "Andenmatten", "Summermatter", "Zurbriggen", "Heinzmann", "Ruppen", "Williner", "Brigger"]

COMPANY_PREFIXES = ["Rhône", "Alpage", "Bisse", "Mazot", "Raccard", "Arolla", "Chablais", "Combin", "Sanetsch", "Vercorin", "Derborence", "Catogne", "Wildhorn", "Bietsch", "Aletsch"]
COMPANY_SUFFIXES = {
    "construction": ["Bâtiment", "Constructions", "Immobilier"],
    "finance": ["Gestion de fortune", "Fiduciaire", "Assurances"],
    "tourism": ["Hôtels", "Tourisme", "Resorts"],
    "wine_food": ["Vins", "Caves", "Saveurs"],
    "energy": ["Énergie", "Solaire", "Hydro"],
    "industry": ["Mécanique", "Industrie", "Ateliers"],
    "tech": ["Digital", "Software", "Data"],
    "health": ["Santé", "Medical", "Physio"],
    "services": ["Conseil", "Avocats", "Partners"],
    "retail": ["Distribution", "Commerce", "Store"],
    "transport": ["Transports", "Logistique", "Express"],
    "media": ["Médias", "Communication", "Studio"],
}
LEGAL_FORMS_FR = ["SA", "Sàrl"]
LEGAL_FORMS_DE = ["AG", "GmbH"]
JOB_TITLES_FR = ["CEO", "CFO", "COO", "Direction générale", "Direction commerciale", "Direction financière", "Gérance", "Présidence du conseil"]
JOB_TITLES_DE = ["CEO", "Geschäftsführung", "Geschäftsleitung", "Verwaltungsratspräsidium"]
REGIONS_FR = ["Martigny", "Sion", "Sierre", "Monthey", "Conthey", "Fully", "Saxon", "Verbier", "Crans-Montana", "Saint-Maurice", "Aigle"]
REGIONS_DE = ["Brig", "Visp", "Naters", "Leuk", "Zermatt", "Saas-Fee"]
TALK_TOPICS = [
    "Recruter des talents en Valais", "La succession d'entreprise", "L'export depuis le Valais",
    "La transition énergétique", "Le tourisme quatre saisons", "Les marchés publics", "L'innovation dans l'artisanat",
    "Le financement des PME", "Le marketing local", "La digitalisation", "Les circuits courts", "L'immobilier en montagne",
]
FUN_FACTS = [
    "A déjà servi une raclette à 200 personnes.", "Parle (presque) couramment le patois d'Évolène.",
    "A gravi le Cervin à 19 ans.", "Collectionne les étiquettes de vin depuis 1998.",
    "A créé sa première entreprise à 22 ans.", "A couru le marathon de New York.", "Joue du cor des Alpes.",
    "A traversé l'Atlantique à la voile.", "Élève des abeilles au-dessus de Sion.",
    "A été figurant dans un film tourné en Valais.", "Connaît tous les cols suisses à moto.",
    "A cuisiné un été dans un restaurant étoilé.", "Fait son propre fromage à l'alpage chaque été.",
    "N'a manqué aucune Foire du Valais depuis 15 ans.", "Pilote d'hélicoptère amateur.",
    "Ancien hockeyeur de bon niveau.", "A vécu cinq ans à Singapour.", "Sait faire une fondue pour 40 personnes.",
    "Organise un tournoi de pétanque chaque été.", "Parle cinq langues, dont le romanche.",
    "A planté sa propre vigne de Cornalin.", "Court Sierre-Zinal chaque année.",
    "Supporte le FC Sion depuis l'enfance.", "Fabrique ses propres skis.",
]
DEMO_PHOTO_KEYS = {
    "camille.rey@example.com": "camille",
    "lukas.imboden@example.com": "lukas",
    "joelle.luisier@example.com": "joelle",
}
