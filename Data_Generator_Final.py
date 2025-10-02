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

#Les def

def quantize_2(x: Decimal) -> Decimal:
    #arrondi a 2
    q = x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if q <= 0:
        raise ValueError("Le prix doit être strictement > 0")
    return q


def to_number(d: Decimal) -> float:
    #Convertit Decimal en float pour JSON
    return float(quantize_2(d))


EMAIL_LIGHT_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def is_email_like(s: str) -> bool:
    #verif mail correct
    if not s or " " in s:
        return False
    return EMAIL_LIGHT_RE.match(s) is not None


def make_valid_email(max_attempts: int = 5) -> str:
    #genere mail et boucle si pas bon.
    for _ in range(max_attempts):
        e = fake.email()
        if is_email_like(e):
            return e
    base = re.sub(r"[^a-z0-9]+", ".", fake.user_name().lower())
    domain = "exemple.fr"
    fallback = f"{base}@{domain}"
    return fallback if is_email_like(fallback) else "utilisateur@exemple.fr"


def paris_now() -> datetime:
    #Datetime actuel Paris
    return datetime.now(ZoneInfo("Europe/Paris"))


def random_delivery_and_expiration(purchase_dt: datetime) -> tuple[date, date]:
    #Génère:
    #delivery_time J+=1-7
    #expiration_time 36-60 mois après achat
    delivery_days = random.randint(1, 7)  
    delivery_time = (purchase_dt.date() + timedelta(days=delivery_days))

    months_add = random.randint(36, 60)
    expiration_dt = purchase_dt + relativedelta(months=+months_add)
    expiration_time = expiration_dt.date()

    if expiration_time < delivery_time:
        expiration_time = delivery_time + timedelta(days=1)

    return delivery_time, expiration_time



# Prix
def calculate_prices(base_price):

    #base_price== 50ml
    #100ml== prix proportionnel
    #30ml== +25% du 50ml
    
    base = Decimal(str(base_price))
    if base <= 0:
        raise ValueError("Le prix de base (50ml) doit être strictement > 0") # on verif mais ok dans dico

    price_per_ml_100 = base / Decimal("50")
    price_100ml = quantize_2(price_per_ml_100 * Decimal("100"))

    price_per_ml_30 = price_per_ml_100 * Decimal("1.25")
    price_30ml = quantize_2(price_per_ml_30 * Decimal("30"))

    return to_number(price_30ml), to_number(price_100ml)


inventory = []
base_inventory = [
    # Florals
    {
        "name": "Rose Poudrée",
        "category": "floral",
        "gender": "f",
        "sub_category": "woody",
        "price": 85.50,
    },
    {
        "name": "Pivoine Céleste",
        "category": "floral",
        "gender": "f",
        "sub_category": "spicy",
        "price": 82.00,
    },
    {
        "name": "Jardin Blanc",
        "category": "floral",
        "gender": "f",
        "sub_category": "sweet",
        "price": 95.00,
    },
    {
        "name": "Fleur de Paris",
        "category": "floral",
        "gender": "f",
        "sub_category": "fresh",
        "price": 90.00,
    },
    {
        "name": "Géranium Noir",
        "category": "floral",
        "gender": "m",
        "sub_category": "amber",
        "price": 78.50,
    },
    {
        "name": "Fleur d'Orange Amère",
        "category": "floral",
        "gender": "m",
        "sub_category": "woody",
        "price": 88.00,
    },
    {
        "name": "Lierre Poivré",
        "category": "floral",
        "gender": "m",
        "sub_category": "spicy",
        "price": 76.00,
    },
    {
        "name": "Pétale de verre",
        "category": "floral",
        "gender": "u",
        "sub_category": "sweet",
        "price": 92.50,
    },
    {
        "name": "Champ de Lin",
        "category": "floral",
        "gender": "u",
        "sub_category": "fresh",
        "price": 75.00,
    },
    {
        "name": "Floraison Blanche",
        "category": "floral",
        "gender": "u",
        "sub_category": "amber",
        "price": 89.00,
    },
    # Woody
    {
        "name": "Bois de Cachemire",
        "category": "woody",
        "gender": "f",
        "sub_category": "floral",
        "price": 110.00,
    },
    {
        "name": "Santal Crème",
        "category": "woody",
        "gender": "f",
        "sub_category": "spicy",
        "price": 125.50,
    },
    {
        "name": "Cèdre Atlas",
        "category": "woody",
        "gender": "m",
        "sub_category": "sweet",
        "price": 105.00,
    },
    {
        "name": "Vétiver Bourbon",
        "category": "woody",
        "gender": "m",
        "sub_category": "fresh",
        "price": 115.00,
    },
    {
        "name": "Bois de Gaïac",
        "category": "woody",
        "gender": "m",
        "sub_category": "amber",
        "price": 120.00,
    },
    {
        "name": "Bois de Oud",
        "category": "woody",
        "gender": "u",
        "sub_category": "floral",
        "price": 150.00,
    },
    {
        "name": "Bois d'Encens",
        "category": "woody",
        "gender": "u",
        "sub_category": "spicy",
        "price": 130.00,
    },
    {
        "name": "Bois de Santal",
        "category": "woody",
        "gender": "u",
        "sub_category": "sweet",
        "price": 128.00,
    },
    # Spicy
    {
        "name": "Ambre Épicé",
        "category": "spicy",
        "gender": "f",
        "sub_category": "floral",
        "price": 98.00,
    },
    {
        "name": "Épices Orientales",
        "category": "spicy",
        "gender": "f",
        "sub_category": "woody",
        "price": 102.50,
    },
    {
        "name": "Poivre Rose",
        "category": "spicy",
        "gender": "f",
        "sub_category": "sweet",
        "price": 94.00,
    },
    {
        "name": "Cardamome Noire",
        "category": "spicy",
        "gender": "m",
        "sub_category": "fresh",
        "price": 99.50,
    },
    {
        "name": "Cannelle Brûlée",
        "category": "spicy",
        "gender": "m",
        "sub_category": "amber",
        "price": 96.00,
    },
    {
        "name": "Gingembre Frais",
        "category": "spicy",
        "gender": "u",
        "sub_category": "floral",
        "price": 85.00,
    },
    {
        "name": "Poivre Noir",
        "category": "spicy",
        "gender": "u",
        "sub_category": "woody",
        "price": 88.00,
    },
    {
        "name": "Safran Précieux",
        "category": "spicy",
        "gender": "u",
        "sub_category": "sweet",
        "price": 140.00,
    },
    # Sweet
    {
        "name": "Vanille Bourbon",
        "category": "sweet",
        "gender": "f",
        "sub_category": "floral",
        "price": 95.00,
    },
    {
        "name": "Fève Tonka",
        "category": "sweet",
        "gender": "f",
        "sub_category": "woody",
        "price": 100.00,
    },
    {
        "name": "Caramel Beurre Salé",
        "category": "sweet",
        "gender": "f",
        "sub_category": "spicy",
        "price": 90.50,
    },
    {
        "name": "Amande Douce",
        "category": "sweet",
        "gender": "m",
        "sub_category": "fresh",
        "price": 85.00,
    },
    {
        "name": "Cacao Intense",
        "category": "sweet",
        "gender": "u",
        "sub_category": "amber",
        "price": 92.00,
    },
    {
        "name": "Fruits Rouges Sucrés",
        "category": "sweet",
        "gender": "u",
        "sub_category": "floral",
        "price": 88.50,
    },
    # Fresh
    {
        "name": "Citron Zesté",
        "category": "fresh",
        "gender": "f",
        "sub_category": "woody",
        "price": 72.00,
    },
    {
        "name": "Bergamote Lumineuse",
        "category": "fresh",
        "gender": "f",
        "sub_category": "spicy",
        "price": 75.00,
    },
    {
        "name": "Mandarine Juteuse",
        "category": "fresh",
        "gender": "f",
        "sub_category": "sweet",
        "price": 74.50,
    },
    {
        "name": "Orange Sanguine",
        "category": "fresh",
        "gender": "m",
        "sub_category": "amber",
        "price": 76.00,
    },
    {
        "name": "Pamplemousse Rose",
        "category": "fresh",
        "gender": "m",
        "sub_category": "floral",
        "price": 77.00,
    },
    {
        "name": "Menthe Fraîche",
        "category": "fresh",
        "gender": "u",
        "sub_category": "woody",
        "price": 69.00,
    },
    {
        "name": "Thé Vert Apaisant",
        "category": "fresh",
        "gender": "u",
        "sub_category": "spicy",
        "price": 79.50,
    },
    # Amber
    {
        "name": "Ambre Impérial",
        "category": "amber",
        "gender": "f",
        "sub_category": "floral",
        "price": 120.00,
    },
    {
        "name": "Ambre Vanillé",
        "category": "amber",
        "gender": "f",
        "sub_category": "woody",
        "price": 125.00,
    },
    {
        "name": "Ambre Oriental",
        "category": "amber",
        "gender": "m",
        "sub_category": "spicy",
        "price": 118.00,
    },
    {
        "name": "Ambre Mystique",
        "category": "amber",
        "gender": "m",
        "sub_category": "sweet",
        "price": 135.00,
    },
    {
        "name": "Ambre Solaire",
        "category": "amber",
        "gender": "u",
        "sub_category": "fresh",
        "price": 115.50,
    },
    {
        "name": "Ambre Boisé",
        "category": "amber",
        "gender": "u",
        "sub_category": "floral",
        "price": 145.00,
    },
]

# Construire variante 30-100ml
for item in base_inventory:
    price_30ml, price_100ml = calculate_prices(item["price"])

    item_30ml = item.copy()
    item_30ml["size"] = "30ml"
    item_30ml["price"] = price_30ml

    item_100ml = item.copy()
    item_100ml["size"] = "100ml"
    item_100ml["price"] = price_100ml

    inventory.append(item_30ml)
    inventory.append(item_100ml)


def print_client_support():
    global inventory, fake

    # Produit
    selected_item = fake.random_element(elements=inventory)

    # Heure d'achat
    purchase_dt = paris_now()

    # Dates
    delivery_time, expiration_time = random_delivery_and_expiration(purchase_dt)

    # 1=lundi - 7=dimanche
    days = purchase_dt.isoweekday()

    refunded = fake.boolean(chance_of_getting_true=10)

    # Champs toujours renseigné pour pouvoir livrer lol
    name = fake.name()
    email = make_valid_email()
    address = {
        "street_address": fake.street_address(),
        "city": fake.city(),
        "postalcode": fake.postcode(),
    }

    # Champs optionnels
    phone = fake.none_or(fake.phone_number())
    emergency_contact = fake.none_or({"name": fake.name(), "phone": fake.phone_number()})

    client_support = {
        "txid": str(uuid.uuid4()),
        "rfid": hex(random.getrandbits(96)),
        "item": selected_item["name"],
        "size": selected_item["size"],
        "category": selected_item["category"],
        "gender": selected_item["gender"],
        "sub_category": selected_item["sub_category"],
        "price": selected_item["price"],
        "purchase_time": purchase_dt.isoformat(),
        "delivery_time": delivery_time.isoformat(),
        "expiration_time": expiration_time.isoformat(),
        "days": days,
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
            if refunded
            else None
        ),
        "review_score": fake.random_int(min=1, max=5),
        "review_text": fake.none_or(fake.sentence(nb_words=12)),
        "name": name,
        "address": address,
        "phone": phone,
        "email": email,
        "emergency_contact": emergency_contact,
    }

    d = json.dumps(client_support) + "\n"
    sys.stdout.write(d)


if __name__ == "__main__":
    
    args = sys.argv[1:]
    if len(args) < 1:
        print("Error: Please provide the number of records to generate as an argument.")
        print("Example: python data_generator.py 100")
        sys.exit(1)

    # Argument obligatoire
    try:
        total_count = int(args[0])
    except ValueError:
        print("Error: Please provide the number of records to generate as an argument.")
        print("Example: python data_generator.py 100")
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
