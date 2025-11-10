# -*- coding: utf-8 -*-
"""
Telegram bot - توليد إيميلات + فحص MX حتى جمع هدف صالح
تعليمات: ثبت الحزم المطلوبة:
  pip install python-telegram-bot requests dnspython
ثم احفظ هذا الملف وشغله.

ملاحظات:
- لإزالة "الرموز الغريبة" نطبع الأسماء بعد إزالة diacritics وتحويلها إلى ASCII.
- يتم توليد دفعات (batch) ثم فحص MX بشكل متوازي، وتحديث رسالة التقدم للمستخدم.
"""

import os
import time
import threading
import random
import re
import unicodedata
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------- إعدادات بسيطة ----------
TOKEN = "8430582466:AAG7d9uFYDAsaGEyeF7eUGqi9xgKdsOGwLY"
ADMINS = {5077182872, 1375521501}

FILES = {
    "USA 🇺🇸": "https://drive.google.com/uc?export=download&id=XXXXXXXXXXXXXXX",
    "UK 🇬🇧": "https://drive.google.com/uc?export=download&id=XXXXXXXXXXXXXXX",
    "Canada 🇨🇦": "https://drive.google.com/uc?export=download&id=XXXXXXXXXXXXXXX",
    "France 🇫🇷": "https://drive.google.com/uc?export=download&id=XXXXXXXXXXXXXXX",
    "Germany 🇩🇪": "https://drive.google.com/uc?export=download&id=XXXXXXXXXXXXXXX"
}

users = set()
last_download = {}

# ---------- بيانات الأسماء والقوائم (مضمّنة) ----------
COUNTRY_NAMES = {
    "usa": {
        "first_names": [
            "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles",
            "Christopher", "Daniel", "Matthew", "Anthony", "Donald", "Mark", "Paul", "Steven", "Andrew", "Kenneth",
            "Joshua", "Kevin", "Brian", "George", "Edward", "Ronald", "Timothy", "Jason", "Jeffrey", "Ryan",
            "Jacob", "Gary", "Nicholas", "Eric", "Jonathan", "Stephen", "Larry", "Justin", "Scott", "Brandon",
            "Benjamin", "Samuel", "Gregory", "Frank", "Alexander", "Raymond", "Patrick", "Jack", "Dennis", "Jerry",
            "Tyler", "Aaron", "Jose", "Adam", "Nathan", "Henry", "Douglas", "Zachary", "Peter", "Kyle",
            "Ethan", "Walter", "Noah", "Jeremy", "Christian", "Keith", "Roger", "Terry", "Austin", "Sean",
            "Carlos", "Bryan", "Luis", "Chad", "Cody", "Jordan", "Cameron", "Devon", "Logan", "Mason",
            "Elijah", "Aiden", "Gabriel", "Caleb", "Isaiah", "Jackson", "Luke", "Hunter", "Jayden", "Owen",
            "Connor", "Isaac", "Landon", "Miles", "Leo", "Theodore", "Roman", "Hudson", "Lincoln", "Eli",
            "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen",
            "Nancy", "Lisa", "Betty", "Margaret", "Sandra", "Ashley", "Kimberly", "Emily", "Donna", "Michelle",
            "Dorothy", "Carol", "Amanda", "Melissa", "Deborah", "Stephanie", "Rebecca", "Laura", "Helen", "Sharon",
            "Cynthia", "Kathleen", "Amy", "Shirley", "Angela", "Anna", "Ruth", "Brenda", "Pamela", "Nicole",
            "Katherine", "Samantha", "Christine", "Emma", "Catherine", "Debra", "Rachel", "Carolyn", "Janet", "Maria",
            "Heather", "Diane", "Julie", "Joyce", "Victoria", "Kelly", "Christina", "Joan", "Evelyn", "Lauren",
            "Judith", "Olivia", "Hannah", "Sophia", "Megan", "Grace", "Amber", "Brittany", "Danielle", "Mia",
            "Chloe", "Natalie", "Ava", "Madison", "Brooklyn", "Zoe", "Lily", "Lillian", "Addison", "Aubrey",
            "Stella", "Nora", "Ellie", "Hazel", "Violet", "Aurora", "Savannah", "Audrey", "Bella", "Claire"
        ],
        "last_names": [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
            "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
            "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson",
            "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
            "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell", "Carter", "Roberts",
            "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker", "Cruz", "Edwards", "Collins", "Reyes",
            "Stewart", "Morris", "Murphy", "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Cooper", "Peterson",
            "Bailey", "Reed", "Kelly", "Howard", "Ramos", "Kim", "Cox", "Ward", "Richardson", "Watson",
            "Brooks", "Chavez", "Wood", "James", "Bennett", "Gray", "Mendoza", "Ruiz", "Hughes", "Price",
            "Alvarez", "Castillo", "Sanders", "Patel", "Myers", "Long", "Ross", "Foster", "Jimenez", "Powell",
            "Jenkins", "Perry", "Russell", "Sullivan", "Bell", "Coleman", "Butler", "Henderson", "Barnes", "Gonzales",
            "Fisher", "Vasquez", "Simmons", "Romero", "Jordan", "Patterson", "Alexander", "Hamilton", "Graham", "Reynolds"
        ]
    },
    "france": {
        "first_names": [
            "Jean", "Pierre", "Michel", "Philippe", "Alain", "Nicolas", "Christophe", "Daniel", "Bernard", "David",
            "Patrick", "Eric", "Laurent", "Thomas", "Romain", "Julien", "Olivier", "François", "Thierry", "Pascal",
            "Jacques", "Mathieu", "Antoine", "Alexandre", "Sébastien", "Cédric", "Lucas", "Baptiste", "Vincent", "Maxime",
            "Guillaume", "Jérémy", "Kevin", "Jonathan", "Raphaël", "Adrien", "Benjamin", "Samuel", "Victor", "Axel",
            "Clément", "Quentin", "Anthony", "Jules", "Hugo", "Arthur", "Louis", "Ethan", "Gabriel", "Nathan",
            "Léo", "Raphaël", "Tom", "Noah", "Enzo", "Liam", "Gabin", "Sacha", "Mohamed", "Paul",
            "Marie", "Julie", "Sarah", "Léa", "Camille", "Pauline", "Marion", "Justine", "Lucie", "Charlotte",
            "Clara", "Emma", "Jade", "Louise", "Alice", "Chloé", "Zoé", "Anna", "Jeanne", "Lina",
            "Eva", "Lola", "Manon", "Célia", "Émilie", "Laura", "Mathilde", "Margaux", "Juliette", "Anaïs",
            "Élodie", "Amandine", "Mélanie", "Alicia", "Océane", "Elisa", "Céline", "Stéphanie", "Caroline", "Nina",
            "Inès", "Léna", "Maëlys", "Romane", "Sofia", "Lilou", "Maeva", "Elise", "Agathe", "Capucine"
        ],
        "last_names": [
            "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy", "Moreau",
            "Simon", "Laurent", "Lefebvre", "Michel", "Garcia", "Bertrand", "Roux", "Vincent", "Fournier", "Morel",
            "Girard", "Dupont", "Lambert", "Bonnet", "Legrand", "Garnier", "Faure", "Rousseau", "Blanc", "Guerin",
            "Muller", "Henry", "Perrin", "Morin", "Dumont", "Chevalier", "François", "Masson", "Marchand", "Caron",
            "Andre", "Lefort", "Mercier", "Deschamps", "Clement", "Gauthier", "Barbier", "Arnaud", "Renard", "Schmitt",
            "Lemoine", "Colin", "Vidal", "Carpentier", "Brun", "Marty", "Blanchard", "Da Silva", "Benoit", "Paris",
            "Bertin", "Boucher", "Fontaine", "Roy", "Leclerc", "Riviere", "Lecomte", "Guillot", "Moulin", "Noel",
            "Berger", "Jacob", "Prevost", "Huet", "Poirier", "Gilles", "Dufour", "Joly", "Lucas", "Brunet"
        ]
    },
    "germany": {
        "first_names": [
            "Thomas", "Michael", "Andreas", "Stefan", "Christian", "Matthias", "Alexander", "Daniel", "Peter", "Frank",
            "Wolfgang", "Ulrich", "Klaus", "Hans", "Ralf", "Martin", "Jan", "Oliver", "Lukas", "Kevin",
            "Sebastian", "Patrick", "Paul", "Tim", "Maximilian", "Leon", "Jonas", "Noah", "Elias", "Ben",
            "Felix", "Julian", "Luca", "David", "Moritz", "Tom", "Philipp", "Simon", "Tobias", "Marcel",
            "Robert", "Fabian", "Marco", "Dominik", "Johannes", "Jannik", "Nico", "Finn", "Luis", "Henry",
            "Emil", "Anton", "Theo", "Oskar", "Jakob", "Samuel", "Jonathan", "Milan", "Benedikt", "Raphael",
            "Anna", "Maria", "Laura", "Sofia", "Emma", "Hannah", "Mia", "Emilia", "Lina", "Lea",
            "Lena", "Leonie", "Julia", "Ida", "Clara", "Amelie", "Mila", "Sophie", "Charlotte", "Luisa",
            "Greta", "Marlene", "Frieda", "Ella", "Marie", "Johanna", "Pia", "Lara", "Nele", "Alina",
            "Nora", "Elisa", "Paula", "Maja", "Helena", "Lilly", "Lisa", "Zoe", "Isabella", "Romy"
        ],
        "last_names": [
            "Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann",
            "Koch", "Bauer", "Richter", "Klein", "Wolf", "Neumann", "Schwarz", "Zimmermann", "Braun", "Krüger",
            "Hartmann", "Lange", "Schmitt", "Werner", "Schäfer", "Krause", "Meier", "Lehmann", "Huber", "Kaiser",
            "Fuchs", "Peters", "Lang", "Scholz", "Möller", "Weiß", "Jung", "Hahn", "Schubert", "Vogel",
            "Friedrich", "Keller", "Günther", "Frank", "Berger", "Winkler", "Roth", "Beck", "Lorenz", "Baumann",
            "Franke", "Albrecht", "Ludwig", "Winter", "Simon", "Lucas", "Schumacher", "Kraus", "Böhm", "Martin",
            "Krämer", "Vogt", "Stein", "Jäger", "Otto", "Sommer", "Groß", "Seidel", "Heinrich", "Brandt",
            "Haas", "Schreiber", "Graf", "Schulte", "Dietrich", "Ziegler", "Kuhn", "Pohl", "Engel", "Horn"
        ]
    },
    "uk": {
        "first_names": [
            "James", "John", "Robert", "Michael", "William", "David", "Richard", "Thomas", "Charles", "Christopher",
            "Daniel", "Matthew", "Anthony", "Mark", "Steven", "Paul", "Andrew", "George", "Edward", "Jack",
            "Henry", "Noah", "Logan", "Dylan", "Mason", "Oliver", "Jacob", "Harry", "Joshua", "Ethan",
            "Joseph", "Samuel", "Benjamin", "Kai", "Luke", "Alexander", "Isaac", "Ryan", "Adam", "Leo",
            "Oscar", "Max", "Archie", "Theo", "Arthur", "Harrison", "Lucas", "Finley", "Riley", "Jude",
            "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Sarah", "Jessica", "Emma", "Olivia", "Sophie",
            "Amelia", "Isla", "Ava", "Emily", "Isabella", "Mia", "Poppy", "Ella", "Grace", "Lily",
            "Evie", "Sophia", "Charlotte", "Daisy", "Freya", "Alice", "Sienna", "Florence", "Chloe", "Ruby",
            "Evelyn", "Maisie", "Phoebe", "Elsie", "Harper", "Matilda", "Ivy", "Rosie", "Luna", "Maya"
        ],
        "last_names": [
            "Smith", "Jones", "Taylor", "Brown", "Williams", "Wilson", "Johnson", "Davies", "Robinson", "Wright",
            "Thompson", "Evans", "Walker", "White", "Roberts", "Green", "Hall", "Wood", "Jackson", "Clarke",
            "Clark", "Harrison", "Lewis", "Scott", "Young", "Morris", "Hall", "Ward", "Turner", "Carter",
            "Phillips", "Mitchell", "Patel", "Adams", "Campbell", "Anderson", "Allen", "Cook", "Bailey", "Parker",
            "Miller", "Davis", "Murphy", "Price", "Bell", "Baker", "Griffiths", "Kelly", "Simpson", "Marshall",
            "Collins", "Bennett", "Cox", "Richardson", "Fox", "Gray", "Rose", "Chapman", "Hunt", "Holmes",
            "Lloyd", "Mason", "Morgan", "Knight", "Butler", "Saunders", "Cole", "Pearce", "Dean", "Foster"
        ]
    },
    "canada": {
        "first_names": [
            "James", "John", "Robert", "Michael", "William", "David", "Richard", "Thomas", "Charles", "Christopher",
            "Daniel", "Matthew", "Anthony", "Mark", "Steven", "Paul", "Andrew", "George", "Mary", "Patricia",
            "Jennifer", "Linda", "Elizabeth", "Sarah", "Jessica", "Karen", "Nancy", "Lisa", "Betty", "Margaret",
            "Sandra", "Ashley", "Kimberly", "Emily", "Donna", "Michelle", "Dorothy", "Carol", "Amanda", "Melissa",
            "Deborah", "Stephanie", "Rebecca", "Laura", "Helen", "Sharon", "Cynthia", "Kathleen", "Amy", "Shirley",
            "Liam", "Noah", "Oliver", "Jack", "Logan", "Lucas", "Benjamin", "Ethan", "Alexander", "Jacob",
            "Samuel", "Daniel", "Henry", "Jackson", "Sebastian", "Aiden", "Matthew", "Samuel", "David", "Joseph",
            "Carter", "Owen", "Wyatt", "Grayson", "Leo", "Jayden", "Gabriel", "Julian", "Muhammad", "Isaac"
        ],
        "last_names": [
            "Smith", "Brown", "Tremblay", "Martin", "Roy", "Gagnon", "Lee", "Wilson", "Johnson", "MacDonald",
            "Taylor", "Campbell", "Anderson", "Jones", "Leblanc", "Côté", "Bouchard", "Gauthier", "Morin", "Pelletier",
            "Lavoie", "Fortin", "Gagné", "Ouellet", "Bélanger", "Lévesque", "Bergeron", "Paquette", "Girard", "Simard",
            "Williams", "Davis", "Miller", "Thompson", "White", "Harris", "Clark", "Lewis", "Robinson", "Walker",
            "Young", "King", "Wright", "Scott", "Green", "Baker", "Adams", "Nelson", "Carter", "Mitchell"
        ]
    },
    "australia": {
        "first_names": [
            "Jack", "Oliver", "William", "Jackson", "Noah", "Lucas", "Thomas", "James", "Liam", "Alexander",
            "Ethan", "Samuel", "Daniel", "Charlie", "Henry", "Joshua", "Harry", "Oscar", "Leo", "Max",
            "Archie", "Isaac", "Mason", "Logan", "Harrison", "Hunter", "Jacob", "Ryan", "Lachlan", "Cooper",
            "Tyler", "Riley", "Zachary", "Billy", "Harley", "Jayden", "Hayden", "Flynn", "Blake", "Ashton",
            "Imogen", "Charlotte", "Olivia", "Mia", "Ava", "Amelia", "Emily", "Isabella", "Sofia", "Chloe",
            "Ella", "Zoe", "Grace", "Ruby", "Lily", "Sophie", "Isla", "Evie", "Harper", "Hannah",
            "Matilda", "Lucy", "Georgia", "Sienna", "Maddison", "Alyssa", "Poppy", "Ivy", "Elsie", "Scarlett",
            "Abigail", "Madison", "Alice", "Eva", "Maya", "Layla", "Aria", "Willow", "Piper", "Ellie"
        ],
        "last_names": [
            "Smith", "Jones", "Williams", "Brown", "Wilson", "Taylor", "Johnson", "White", "Martin", "Anderson",
            "Thompson", "Nguyen", "Walker", "Harris", "Lee", "Ryan", "Robinson", "Kelly", "King", "Davis",
            "Wright", "Evans", "Thomas", "Roberts", "Green", "Hall", "Wood", "Jackson", "Turner", "Clark",
            "Harrison", "Scott", "Mitchell", "Hill", "Moore", "Murphy", "Graham", "McDonald", "Knight", "Butler",
            "Webb", "Watson", "Baker", "Cook", "Edwards", "Murray", "Reid", "Marshall", "Stewart", "Fisher"
        ]
    },
    "international": {
        "first_names": [
            "David", "Michael", "Chris", "Daniel", "James", "Robert", "John", "Paul", "Mark", "Steven",
            "Andrew", "Kevin", "Brian", "Jason", "Matthew", "Richard", "Thomas", "Maria", "Anna", "Laura",
            "Sarah", "Lisa", "Nancy", "Jennifer", "Linda", "Elizabeth", "Susan", "Jessica", "Karen", "Betty",
            "Helen", "Margaret", "Sandra", "Donna", "Carol", "Ruth", "Sharon", "Michelle", "Laura", "Amanda",
            "Melissa", "Rebecca", "Dorothy", "Cynthia", "Kathleen", "Amy", "Shirley", "Angela", "Emma", "Olivia",
            "Sophia", "Isabella", "Mia", "Charlotte", "Amelia", "Evelyn", "Abigail", "Harper", "Emily", "Ella",
            "Avery", "Sofia", "Camila", "Aria", "Scarlett", "Victoria", "Madison", "Luna", "Grace", "Chloe",
            "Penelope", "Layla", "Riley", "Zoey", "Nora", "Lily", "Eleanor", "Hannah", "Lillian", "Addison"
        ],
        "last_names": [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Garcia", "Rodriguez", "Wilson",
            "Martinez", "Anderson", "Taylor", "Thomas", "Hernandez", "Moore", "Martin", "Jackson", "Thompson", "White",
            "Lopez", "Lee", "Gonzalez", "Harris", "Clark", "Lewis", "Robinson", "Walker", "Perez", "Hall",
            "Young", "Allen", "Sanchez", "Wright", "King", "Scott", "Green", "Baker", "Adams", "Nelson",
            "Hill", "Ramirez", "Campbell", "Mitchell", "Roberts", "Carter", "Phillips", "Evans", "Turner", "Torres",
            "Parker", "Collins", "Edwards", "Stewart", "Flores", "Morris", "Nguyen", "Murphy", "Rivera", "Cook",
            "Rogers", "Morgan", "Peterson", "Cooper", "Reed", "Bailey", "Bell", "Gomez", "Kelly", "Howard"
        ]
    }
}

DOMAIN_LISTS = {
    "france": [
        "orange.fr", "free.fr", "sfr.fr", "gmail.com", "yahoo.fr",
        "hotmail.fr", "laposte.net", "wanadoo.fr", "neuf.fr", "live.fr",
        "outlook.fr", "bbox.fr", "numericable.fr", "aliceadsl.fr", "club-internet.fr"
    ],
    "germany": [
        "gmail.com", "web.de", "gmx.de", "hotmail.de", "yahoo.de",
        "t-online.de", "freenet.de", "arcor.de", "outlook.de", "live.de"
    ],
    "uk": [
        "gmail.com", "yahoo.co.uk", "hotmail.co.uk", "outlook.com",
        "btinternet.com", "blueyonder.co.uk", "live.co.uk", "ntlworld.com",
        "virginmedia.com", "talktalk.net"
    ],
    "canada": [
        "gmail.com", "yahoo.ca", "hotmail.com", "outlook.com",
        "sympatico.ca", "rogers.com", "bell.net", "telus.net",
        "shaw.ca", "videotron.ca"
    ],
    "australia": [
        "gmail.com", "yahoo.com.au", "hotmail.com", "outlook.com",
        "bigpond.com", "optusnet.com.au", "iinet.net.au", "internode.on.net"
    ],
    "international": [
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
        "protonmail.com", "mail.com", "zoho.com", "yandex.com",
        "gmx.com", "hubspot.com"
    ],
    "usa": [
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com",
        "comcast.net", "verizon.net", "att.net", "icloud.com", "msn.com",
        "live.com", "rocketmail.com", "ymail.com", "gmx.com", "mail.com",
        "protonmail.com", "zoho.com", "yandex.com", "inbox.com", "fastmail.com"
    ]
}

DISPOSABLE_DOMAINS = {"mailinator.com","10minutemail.com","tempmail.com","trashmail.com","guerrillamail.com","yopmail.com","getnada.com"}
ROLE_LOCAL_PARTS = {"admin","administrator","postmaster","abuse","support","info","sales","contact","billing","security","webmaster","noreply","no-reply","team","customerservice"}

EMAIL_REGEX = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')

# Patterns and weights (كما طلبت)
PATTERNS = [
    ("{first}.{last}", 35),
    ("{first}{last}", 25),
    ("{first}_{last}", 15),
    ("{f}.{last}", 10),
    ("{first}{l}", 8),
    ("{first}{num}", 7)
]

NUMBER_WEIGHTED = [
    ("birth_year", 45),
    ("age", 20),
    ("small", 15),
    ("area", 10),
    ("none", 10)
]

def choose_pattern():
    patterns, weights = zip(*PATTERNS)
    return random.choices(patterns, weights=weights, k=1)[0]

def choose_number():
    types, weights = zip(*NUMBER_WEIGHTED)
    choice = random.choices(types, weights=weights, k=1)[0]
    if choice == "birth_year":
        return str(random.randint(1970, 2005))
    if choice == "age":
        return str(random.choice([25,30,35,40,45]))
    if choice == "small":
        return str(random.randint(1,99))
    if choice == "area":
        return random.choice(["202","212","310","415","305","617","718","213","312","646"])
    return ""

def ascii_normalize(s):
    """حذف العلامات (diacritics) وتحويل للحروف ASCII فقط وصرف الغير مقبول."""
    if not s:
        return ""
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')
    s = s.encode('ascii', 'ignore').decode('ascii')
    s = s.lower()
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

def syntax_check(email):
    return EMAIL_REGEX.match(email) is not None

def disposable_check(domain):
    d = domain.lower()
    return d in DISPOSABLE_DOMAINS or any(dd in d for dd in DISPOSABLE_DOMAINS)

def mx_check(domain):
    try:
        import dns.resolver
    except Exception as e:
        raise RuntimeError("Missing dependency 'dnspython'. Install with: pip install dnspython") from e
    try:
        answers = dns.resolver.resolve(domain, 'MX', lifetime=5)
        return len(answers) > 0
    except Exception:
        return False

def role_check(local_part):
    lp = local_part.lower()
    if lp in ROLE_LOCAL_PARTS:
        return False
    for r in ROLE_LOCAL_PARTS:
        if lp.startswith(r):
            return False
    return True

def generate_single_local(first, last):
    pattern = choose_pattern()
    num = choose_number()
    f = ascii_normalize(first)
    l = ascii_normalize(last)
    local = pattern.format(first=f, last=l, f=f[0] if f else '', l=l[0] if l else '', num=num)
    local = re.sub(r'\.+', '.', local).strip('.')
    if local == "":
        local = f"{f}{l}"
    return local

def generate_candidates_batch(firsts, lasts, domain, batch_size=200):
    candidates = []
    for _ in range(batch_size):
        first = random.choice(firsts)
        last = random.choice(lasts)
        local = generate_single_local(first, last)
        email = f"{local}@{domain}"
        candidates.append(email)
    return candidates

def validate_emails_mx_batch(emails, max_workers=30):
    """تفترض أن الإدخال قائمة إيميلات؛ تقوم بفحص MX بشكل متوازي وتعيد (valid, invalid)."""
    valid = []
    invalid = []
    domain_cache = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_email = {}
        for email in emails:
            dom = email.split('@')[1]
            if dom in domain_cache:
                if domain_cache[dom]:
                    valid.append(email)
                else:
                    invalid.append(email)
                continue
            future_to_email[executor.submit(mx_check, dom)] = email
        for fut in as_completed(future_to_email):
            email = future_to_email[fut]
            try:
                ok = fut.result()
            except Exception:
                ok = False
            dom = email.split('@')[1]
            domain_cache[dom] = ok
            if ok:
                valid.append(email)
            else:
                invalid.append(email)
    return valid, invalid

def display_name_to_code(display_name):
    key = display_name.split()[0].lower()
    if key == "usa":
        return "usa"
    return key

def keep_alive():
    while True:
        print("💡 [KEEP-ALIVE] Bot is running smoothly.")
        time.sleep(3600)

# ---------------- Handlers ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    users.add(user_id)
    keyboard = [[InlineKeyboardButton(country, callback_data=f"COUNTRY|{country}")] for country in FILES.keys()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 Welcome!\n\nSelect a country to generate emails.\nYou can only use this feature once every 24 hours.", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    now = datetime.now()

    if user_id in last_download and now - last_download[user_id] < timedelta(hours=24):
        remaining = timedelta(hours=24) - (now - last_download[user_id])
        hours = int(remaining.total_seconds() // 3600)
        await query.edit_message_text(f"⏳ You already used your daily limit.\nTry again in {hours} hours.")
        return

    if data.startswith("COUNTRY|"):
        display_country = data.split("|",1)[1]
        country_code = display_name_to_code(display_country)
        domains = DOMAIN_LISTS.get(country_code, DOMAIN_LISTS.get("international", []))
        keyboard = [[InlineKeyboardButton(d, callback_data=f"DOMAIN|{country_code}|{d}")] for d in domains]
        keyboard.append([
            InlineKeyboardButton("Generate 100", callback_data=f"COUNT|{country_code}|100"),
            InlineKeyboardButton("Generate 1000", callback_data=f"COUNT|{country_code}|1000"),
            InlineKeyboardButton("Generate 10000", callback_data=f"COUNT|{country_code}|10000"),
        ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"🌍 {display_country}\nChoose a domain (or choose a count — you'll be asked next):", reply_markup=reply_markup)
        return

    if data.startswith("COUNT|"):
        _, country_code, count_str = data.split("|")
        domains = DOMAIN_LISTS.get(country_code, DOMAIN_LISTS.get("international", []))
        keyboard = [[InlineKeyboardButton(d, callback_data=f"DOMAIN|{country_code}|{d}|{count_str}")] for d in domains]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"📊 You chose to generate {count_str} emails.\nPlease choose a domain:", reply_markup=reply_markup)
        return

    if data.startswith("DOMAIN|"):
        parts = data.split("|")
        country_code = parts[1]
        domain = parts[2]
        count = 10000
        if len(parts) > 3 and parts[3].isdigit():
            count = int(parts[3])

        # ارسل رسالة أولية ثم ابدأ المهمة الخلفية
        status_msg = await query.edit_message_text(f"⏳ Starting generation and validation for {count} valid emails on domain {domain}...\nGenerating Mail in progress: 0/{count}")
        await context.application.create_task(_generate_until_target_and_send(user_id, country_code, domain, count, context, status_msg))
        last_download[user_id] = now
        return

    await query.edit_message_text("❌ Unknown action.")

async def _generate_until_target_and_send(user_id, country_code, domain, target_count, context, status_message):
    """
    توليد + فحص حتى نجمع target_count إيميل صالح.
    نولد دفعات، نفرز محلياً (syntax/role/disposable/تكرار)، ثم نفحص MX دفعة بدفعة.
    نحدّث رسالة التقدم (editable) أثناء العمل.
    """
    try:
        pool = COUNTRY_NAMES.get(country_code, COUNTRY_NAMES.get("international"))
        firsts = pool["first_names"]
        lasts = pool["last_names"]
        collected = set()
        attempts = 0
        batch_size = 200
        max_attempts = target_count * 50

        # progress message (نستخدم الرسالة المعدلة مسبقاً إن أمكن)
        progress_msg = status_message

        last_update = time.time()
        while len(collected) < target_count and attempts < max_attempts:
            candidates = generate_candidates_batch(firsts, lasts, domain, batch_size=batch_size)

            # local filters: syntax, role, disposable, uniqueness
            filtered = []
            for e in candidates:
                if e in collected:
                    continue
                if not syntax_check(e):
                    continue
                local = e.split('@')[0]
                if not role_check(local):
                    continue
                if disposable_check(domain):
                    continue
                filtered.append(e)

            if not filtered:
                attempts += batch_size
                if time.time() - last_update > 2:
                    try:
                        await context.bot.edit_message_text(chat_id=user_id, message_id=progress_msg.message_id, text=f"Generating Mail in progress: {len(collected)}/{target_count}")
                    except Exception:
                        pass
                    last_update = time.time()
                continue

            # MX validation for filtered candidates
            valid_chunk, invalid_chunk = validate_emails_mx_batch(filtered, max_workers=30)
            for v in valid_chunk:
                if len(collected) >= target_count:
                    break
                collected.add(v)
            attempts += len(filtered)

            # تحديث التقدم للمستخدم
            if time.time() - last_update > 1 or len(collected) % 25 == 0:
                try:
                    await context.bot.edit_message_text(chat_id=user_id, message_id=progress_msg.message_id, text=f"Generating Mail in progress: {len(collected)}/{target_count}")
                except Exception:
                    pass
                last_update = time.time()

        total_collected = len(collected)
        filename = f"{country_code}_{domain.replace('.', '_')}_{int(time.time())}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            for e in collected:
                f.write(e + "\n")

        if total_collected == 0:
            await context.bot.send_message(chat_id=user_id, text=f"❌ Finished but no valid emails were collected. Attempts: {attempts}")
        else:
            await context.bot.send_message(chat_id=user_id, text=f"✅ Finished. Collected: {total_collected} valid emails. Sending file...")
            await context.bot.send_document(chat_id=user_id, document=open(filename, "rb"))
        print(f"[INFO] User {user_id} received file {filename} (collected={total_collected})")
    except Exception as e:
        print(f"[ERROR] Generation error: {e}")
        try:
            await context.bot.send_message(chat_id=user_id, text=f"❌ Error during generation: {e}")
        except:
            pass

# Broadcast & stats (من الكود الأصلي)
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        await update.message.reply_text("🚫 You are not authorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <your message>")
        return
    message = " ".join(context.args)
    sent = 0
    for user in list(users):
        try:
            await context.bot.send_message(chat_id=user, text=f"📢 Admin Message:\n\n{message}")
            sent += 1
        except:
            pass
    await update.message.reply_text(f"✅ Broadcast sent to {sent} users.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        await update.message.reply_text("🚫 You are not authorized.")
        return
    await update.message.reply_text(f"👥 Total users: {len(users)}")

# Main
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("stats", stats))
    threading.Thread(target=keep_alive, daemon=True).start()
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()