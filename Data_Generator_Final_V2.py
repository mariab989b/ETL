# les imports

import sys
import json
import optional_faker as _
import uuid
import random
import re

from decimal import Decimal, ROUND_HALF_UP
from dotenv import load_dotenv
from faker import Faker
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from zoneinfo import ZoneInfo


load_dotenv()
fake = Faker("fr_FR")  


# Utilitaires 

def quantize_2(x: Decimal) -> Decimal:
    #arrondi
    q = x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if q <= 0:
        raise ValueError("Le prix doit être strictement > 0")
    return q

def to_number(d: Decimal) -> float:
    #Convertit Decimal en float
    return float(quantize_2(d))

EMAIL_LIGHT_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def is_email_like(s: str) -> bool:
    #Vérification email
    if not s or " " in s:
        return False
    return EMAIL_LIGHT_RE.match(s) is not None

def make_valid_email(max_attempts: int = 5) -> str:
    #Génère un email via Faker et vérifie la forme; boucle quelques fois au besoin
    for _ in range(max_attempts):
        e = fake.email()
        if is_email_like(e):
            return e
    base = re.sub(r"[^a-z0-9]+", ".", fake.user_name().lower())
    domain = "exemple.fr"
    fallback = f"{base}@{domain}"
    return fallback if is_email_like(fallback) else "utilisateur@exemple.fr"

def paris_now() -> datetime:
    """Datetime actuel en Europe/Paris (aware)."""
    return datetime.now(ZoneInfo("Europe/Paris"))

def random_delivery_and_expiration(purchase_dt: datetime) -> tuple[date, date]:
    
    #delivery_time J+=1-7
    #expiration_time J+=36-60 après achat
    
    delivery_days = random.randint(1, 7) 
    delivery_time = (purchase_dt.date() + timedelta(days=delivery_days))

    months_add = random.randint(36, 60) 
    expiration_dt = purchase_dt + relativedelta(months=+months_add)
    expiration_time = expiration_dt.date()

    # expiration >= livraison
    if expiration_time < delivery_time:
        expiration_time = delivery_time + timedelta(days=1)

    return delivery_time, expiration_time

def stable_product_id(product_name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, product_name.strip().lower()))

def make_variant_id(product_id: str, size_str: str) -> str:
    
    #Concatène product_id + '_' + taille    
    size_code = ''.join(ch for ch in size_str if ch.isdigit()) or size_str
    return f"{product_id}_{size_code}"

#generation text review
def get_review_text(score: int) -> str:
    positive_words = ["excellent", "agréable", "magnifique", "superbe", "élégant", "raffiné"]
    negative_words = ["décevant", "médiocre", "désagréable", "faible", "mauvais", "fade"]
    neutral_words = ["correct", "moyen", "standard", "basique", "ordinaire"]

    aspects = ["parfum", "fragrance", "tenue", "notes", "odeur", "qualité"]
    feelings = ["trouve", "pense", "considère", "estime", "trouve que"]

    if score == 1:
        return f"Je {fake.random_element(feelings)} ce {fake.random_element(aspects)} {fake.random_element(negative_words)} et vraiment {fake.random_element(negative_words)}."
    elif score == 2:
        return f"Je {fake.random_element(feelings)} que ce {fake.random_element(aspects)} est plutôt {fake.random_element(negative_words)}."
    elif score == 3:
        return f"Je {fake.random_element(feelings)} que ce {fake.random_element(aspects)} est {fake.random_element(neutral_words)}."
    elif score == 4:
        return f"Je {fake.random_element(feelings)} ce {fake.random_element(aspects)} vraiment {fake.random_element(positive_words)}."
    else:  # score == 5
        return f"Je {fake.random_element(feelings)} ce {fake.random_element(aspects)} {fake.random_element(positive_words)} et absolument {fake.random_element(positive_words)}!"

#prix
def calculate_prices(base_price):
    
    #100ml : prix proportionnel
    #30ml : 25% plus cher au ml que 50ml
    
    base = Decimal(str(base_price))
    if base <= 0:
        raise ValueError("Le prix de base (50ml) doit être strictement > 0")

    price_per_ml_100 = base / Decimal("50")
    price_100ml = quantize_2(price_per_ml_100 * Decimal("100"))

    price_per_ml_30 = price_per_ml_100 * Decimal("1.25")
    price_30ml = quantize_2(price_per_ml_30 * Decimal("30"))

    return to_number(price_30ml), to_number(price_100ml)


# Catalogue 

inventory = []
base_inventory = [
    # Florals
    {"name": "Rose Poudrée", "category": "floral", "gender": "f", "sub_category": "woody", "price": 85.50},
    {"name": "Pivoine Céleste", "category": "floral", "gender": "f", "sub_category": "spicy", "price": 82.00},
    {"name": "Jardin Blanc", "category": "floral", "gender": "f", "sub_category": "sweet", "price": 95.00},
    {"name": "Fleur de Paris", "category": "floral", "gender": "f", "sub_category": "fresh", "price": 90.00},
    {"name": "Géranium Noir", "category": "floral", "gender": "m", "sub_category": "amber", "price": 78.50},
    {"name": "Fleur d'Orange Amère", "category": "floral", "gender": "m", "sub_category": "woody", "price": 88.00},
    {"name": "Lierre Poivré", "category": "floral", "gender": "m", "sub_category": "spicy", "price": 76.00},
    {"name": "Pétale de verre", "category": "floral", "gender": "u", "sub_category": "sweet", "price": 92.50},
    {"name": "Champ de Lin", "category": "floral", "gender": "u", "sub_category": "fresh", "price": 75.00},
    {"name": "Floraison Blanche", "category": "floral", "gender": "u", "sub_category": "amber", "price": 89.00},
    # Woody
    {"name": "Bois de Cachemire", "category": "woody", "gender": "f", "sub_category": "floral", "price": 110.00},
    {"name": "Santal Crème", "category": "woody", "gender": "f", "sub_category": "spicy", "price": 125.50},
    {"name": "Cèdre Atlas", "category": "woody", "gender": "m", "sub_category": "sweet", "price": 105.00},
    {"name": "Vétiver Bourbon", "category": "woody", "gender": "m", "sub_category": "fresh", "price": 115.00},
    {"name": "Bois de Gaïac", "category": "woody", "gender": "m", "sub_category": "amber", "price": 120.00},
    {"name": "Bois de Oud", "category": "woody", "gender": "u", "sub_category": "floral", "price": 150.00},
    {"name": "Bois d'Encens", "category": "woody", "gender": "u", "sub_category": "spicy", "price": 130.00},
    {"name": "Bois de Santal", "category": "woody", "gender": "u", "sub_category": "sweet", "price": 128.00},
    # Spicy
    {"name": "Ambre Épicé", "category": "spicy", "gender": "f", "sub_category": "floral", "price": 98.00},
    {"name": "Épices Orientales", "category": "spicy", "gender": "f", "sub_category": "woody", "price": 102.50},
    {"name": "Poivre Rose", "category": "spicy", "gender": "f", "sub_category": "sweet", "price": 94.00},
    {"name": "Cardamome Noire", "category": "spicy", "gender": "m", "sub_category": "fresh", "price": 99.50},
    {"name": "Cannelle Brûlée", "category": "spicy", "gender": "m", "sub_category": "amber", "price": 96.00},
    {"name": "Gingembre Frais", "category": "spicy", "gender": "u", "sub_category": "floral", "price": 85.00},
    {"name": "Poivre Noir", "category": "spicy", "gender": "u", "sub_category": "woody", "price": 88.00},
    {"name": "Safran Précieux", "category": "spicy", "gender": "u", "sub_category": "sweet", "price": 140.00},
    # Sweet
    {"name": "Vanille Bourbon", "category": "sweet", "gender": "f", "sub_category": "floral", "price": 95.00},
    {"name": "Fève Tonka", "category": "sweet", "gender": "f", "sub_category": "woody", "price": 100.00},
    {"name": "Caramel Beurre Salé", "category": "sweet", "gender": "f", "sub_category": "spicy", "price": 90.50},
    {"name": "Amande Douce", "category": "sweet", "gender": "m", "sub_category": "fresh", "price": 85.00},
    {"name": "Cacao Intense", "category": "sweet", "gender": "u", "sub_category": "amber", "price": 92.00},
    {"name": "Fruits Rouges Sucrés", "category": "sweet", "gender": "u", "sub_category": "floral", "price": 88.50},
    # Fresh
    {"name": "Citron Zesté", "category": "fresh", "gender": "f", "sub_category": "woody", "price": 72.00},
    {"name": "Bergamote Lumineuse", "category": "fresh", "gender": "f", "sub_category": "spicy", "price": 75.00},
    {"name": "Mandarine Juteuse", "category": "fresh", "gender": "f", "sub_category": "sweet", "price": 74.50},
    {"name": "Orange Sanguine", "category": "fresh", "gender": "m", "sub_category": "amber", "price": 76.00},
    {"name": "Pamplemousse Rose", "category": "fresh", "gender": "m", "sub_category": "floral", "price": 77.00},
    {"name": "Menthe Fraîche", "category": "fresh", "gender": "u", "sub_category": "woody", "price": 69.00},
    {"name": "Thé Vert Apaisant", "category": "fresh", "gender": "u", "sub_category": "spicy", "price": 79.50},
    # Amber
    {"name": "Ambre Impérial", "category": "amber", "gender": "f", "sub_category": "floral", "price": 120.00},
    {"name": "Ambre Vanillé", "category": "amber", "gender": "f", "sub_category": "woody", "price": 125.00},
    {"name": "Ambre Oriental", "category": "amber", "gender": "m", "sub_category": "spicy", "price": 118.00},
    {"name": "Ambre Mystique", "category": "amber", "gender": "m", "sub_category": "sweet", "price": 135.00},
    {"name": "Ambre Solaire", "category": "amber", "gender": "u", "sub_category": "fresh", "price": 115.50},
    {"name": "Ambre Boisé", "category": "amber", "gender": "u", "sub_category": "floral", "price": 145.00},
]

#variantes 30ml / 100ml
for item in base_inventory:
    price_30ml, price_100ml = calculate_prices(item["price"])

    # ID produit général
    pid = stable_product_id(item["name"])

    item_30ml = item.copy()
    item_30ml["size"] = "30ml"
    item_30ml["price"] = price_30ml
    item_30ml["product_id"] = pid
    item_30ml["product_variant_id"] = make_variant_id(pid, item_30ml["size"])

    item_100ml = item.copy()
    item_100ml["size"] = "100ml"
    item_100ml["price"] = price_100ml
    item_100ml["product_id"] = pid
    item_100ml["product_variant_id"] = make_variant_id(pid, item_100ml["size"])

    inventory.append(item_30ml)
    inventory.append(item_100ml)


# Génération
def print_client_support():
    global inventory, fake

    selected_item = fake.random_element(elements=inventory)

    # Heure paris
    purchase_dt = paris_now()

    # Dates cohérentes
    delivery_time, expiration_time = random_delivery_and_expiration(purchase_dt)

    # 1=lundi..7=dimanche
    days = purchase_dt.isoweekday()

    refunded = fake.boolean(chance_of_getting_true=10)

    # 
    name = fake.name()
    email = make_valid_email()
    address = {
        "street_address": fake.street_address(),
        "city": fake.city(),
        "postalcode": fake.postcode(),
    }

    # infos client perso
    # Date de naissance
    dob_start = purchase_dt.date() - relativedelta(years=80)
    dob_end = purchase_dt.date() - relativedelta(years=18)
    date_of_birth = fake.date_between_dates(dob_start, dob_end).isoformat()

    sex = fake.random_element(elements=["m", "f", "x"])

    # Champs optionnels
    phone = fake.none_or(fake.phone_number())
    review_score = fake.random_int(min=1, max=5)
    # review_text
    review_text = fake.none_or(get_review_text(review_score))

    client_support = {
        # IDs techniques
        "txid": str(uuid.uuid4()),
        "rfid": hex(random.getrandbits(96)),

        # Produit + IDs produits
        "product_id": selected_item["product_id"],                 
        "product_variant_id": selected_item["product_variant_id"], 
        "item": selected_item["name"],
        "size": selected_item["size"],
        "category": selected_item["category"],
        "gender": selected_item["gender"],
        "sub_category": selected_item["sub_category"],
        "price": selected_item["price"],  

        # Temps
        "purchase_time": purchase_dt.isoformat(),
        "delivery_time": delivery_time.isoformat(),
        "expiration_time": expiration_time.isoformat(),

        # Jour semaine (1..7)
        "days": days,

        # Remboursement
        "refunded": refunded,
        "refund_reason": (
            fake.random_element(
                elements=[
                    "Produit endommagé",
                    "Mauvais article envoyé",
                    "Produit non conforme",
                    "Meilleur prix ailleurs",
                    "Changement d'avis",
                ]
            )
            if refunded else None
        ),

        # Avis
        "review_score": review_score,
        "review_text": review_text,

        # Client 
        "name": name,
        "address": address,
        "phone": phone,
        "email": email,
        "date_of_birth": date_of_birth,
        "sex": sex,
    }

    d = json.dumps(client_support) + "\n"
    sys.stdout.write(d)


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 1:
        print("Error: Please provide the number of records to generate as an argument.")
        print("Example: python Data_generator.py 100")
        sys.exit(1)

    try:
        total_count = int(args[0])
    except ValueError:
        print("Error: Please provide the number of records to generate as an argument.")
        print("Example: python Data_generator.py 100")
        sys.exit(1)

    # Option --seed
    seed = None
    if len(args) >= 2:
        if args[1].startswith("--seed="):
            _, s = args[1].split("=", 1)
            seed = int(s)
        elif args[1] == "--seed" and len(args) >= 3:
            seed = int(args[2])

    if seed is not None:
        random.seed(seed)
        Faker.seed(seed)

    for _ in range(total_count):
        print_client_support()
    print("")
