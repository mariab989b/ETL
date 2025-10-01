import sys
import json
import optional_faker as _
import uuid
import random

from dotenv import load_dotenv
from faker import Faker
from datetime import date, datetime

load_dotenv()
fake = Faker()


def calculate_prices(base_price):
    # Assume base_price is for 50ml, scale accordingly
    price_per_ml_100 = base_price / 50
    price_100ml = round(price_per_ml_100 * 100, 2)
    price_per_ml_30 = price_per_ml_100 * 1.25  # 25% more expensive per ml
    price_30ml = round(price_per_ml_30 * 30, 2)
    return price_30ml, price_100ml


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
    state = fake.state_abbr()

    # Select a random item (which is now a dictionary) from the inventory
    selected_item = fake.random_element(elements=inventory)

    client_support = {
        "txid": str(uuid.uuid4()),
        "rfid": hex(random.getrandbits(96)),
        "item": selected_item["name"],  # Extract the name from the dictionary
        "size": selected_item["size"],
        "category": selected_item["category"],
        "gender": selected_item["gender"],
        "sub_category": selected_item["sub_category"],
        "price": selected_item["price"],  # Extract the price from the dictionary
        "purchase_time": datetime.utcnow().isoformat(),
        "delivery_time": date(2025, 9, 29).isoformat(),  # Delivery date,
        "expiration_time": date(2026, 9, 29).isoformat(),  # Expiration date,
        "days": fake.random_int(min=1, max=7),
        "refunded": fake.boolean(chance_of_getting_true=10),
        "refund_reason": (
            fake.random_element(
                elements=[
                    "Damaged item",
                    "Wrong item sent",
                    "Item not as described",
                    "Better price available",
                    "Changed mind",
                ]
            )
            if client_support.get("refunded", False)  # noqa: F821
            else None
        ),
        "review_score": fake.random_int(min=1, max=5),
        "review_text": fake.sentence(nb_words=12),
        "name": fake.name(),
        "address": fake.none_or(
            {
                "street_address": fake.street_address(),
                "city": fake.city(),
                "state": state,
                "postalcode": fake.postalcode_in_state(state),
            }
        ),
        "phone": fake.none_or(fake.phone_number()),
        "email": fake.none_or(fake.email()),
        "emergency_contact": fake.none_or(
            {"name": fake.name(), "phone": fake.phone_number()}
        ),
    }
    d = json.dumps(client_support) + "\n"
    sys.stdout.write(d)


if __name__ == "__main__":
    args = sys.argv[1:]
    if len(args) < 1:
        print("Error: Please provide the number of records to generate as an argument.")
        print("Example: python data_generator.py 100")
        sys.exit(1)

    total_count = int(args[0])
    for _ in range(total_count):
        print_client_support()
    print("")
