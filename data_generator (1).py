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
inventory = inventory = [
    # Florals
    {"name": "Rose Poudrée", "details": "(f,floral)", "price": 85.50},
    {"name": "Pivoine Céleste", "details": "(f,floral)", "price": 82.00},
    {"name": "Jardin Blanc", "details": "(f,floral)", "price": 95.00},
    {"name": "Fleur de Paris", "details": "(f,floral)", "price": 90.00},
    {"name": "Géranium Noir", "details": "(m, floral)", "price": 78.50},
    {"name": "Fleur d'Orange Amère", "details": "(m, floral)", "price": 88.00},
    {"name": "Lierre Poivré", "details": "(m, floral)", "price": 76.00},
    {"name": "Pétale de verre", "details": "(u, floral)", "price": 92.50},
    {"name": "Champ de Lin", "details": "(u, floral)", "price": 75.00},
    {"name": "Floraison Blanche", "details": "(u, floral)", "price": 89.00},
    # Woody
    {"name": "Bois de Cachemire", "details": "(f, woody)", "price": 110.00},
    {"name": "Santal Crème", "details": "(f, woody)", "price": 125.50},
    {"name": "Cèdre Atlas", "details": "(m, woody)", "price": 105.00},
    {"name": "Vétiver Bourbon", "details": "(m, woody)", "price": 115.00},
    {"name": "Bois de Gaïac", "details": "(m, woody)", "price": 120.00},
    {"name": "Bois de Oud", "details": "(u, woody)", "price": 150.00},
    {"name": "Bois d'Encens", "details": "(u, woody)", "price": 130.00},
    {"name": "Bois de Santal", "details": "(u, woody)", "price": 128.00},
    # Spicy
    {"name": "Ambre Épicé", "details": "(f, spicy)", "price": 98.00},
    {"name": "Épices Orientales", "details": "(f, spicy)", "price": 102.50},
    {"name": "Poivre Rose", "details": "(f, spicy)", "price": 94.00},
    {"name": "Cardamome Noire", "details": "(m, spicy)", "price": 99.50},
    {"name": "Cannelle Brûlée", "details": "(m, spicy)", "price": 96.00},
    {"name": "Gingembre Frais", "details": "(u, spicy)", "price": 85.00},
    {"name": "Poivre Noir", "details": "(u, spicy)", "price": 88.00},
    {"name": "Safran Précieux", "details": "(u, spicy)", "price": 140.00},
    # Sweet
    {"name": "Vanille Bourbon", "details": "(f, sweet)", "price": 95.00},
    {"name": "Fève Tonka", "details": "(f, sweet)", "price": 100.00},
    {"name": "Caramel Beurre Salé", "details": "(f, sweet)", "price": 90.50},
    {"name": "Amande Douce", "details": "(m, sweet)", "price": 85.00},
    {"name": "Cacao Intense", "details": "(u, sweet)", "price": 92.00},
    {"name": "Fruits Rouges Sucrés", "details": "(u, sweet)", "price": 88.50},
    # Fresh
    {"name": "Citron Zesté", "details": "(f, fresh)", "price": 72.00},
    {"name": "Bergamote Lumineuse", "details": "(f, fresh)", "price": 75.00},
    {"name": "Mandarine Juteuse", "details": "(f, fresh)", "price": 74.50},
    {"name": "Orange Sanguine", "details": "(m, fresh)", "price": 76.00},
    {"name": "Pamplemousse Rose", "details": "(m, fresh)", "price": 77.00},
    {"name": "Menthe Fraîche", "details": "(u, fresh)", "price": 69.00},
    {"name": "Thé Vert Apaisant", "details": "(u, fresh)", "price": 79.50},
    # Amber
    {"name": "Ambre Impérial", "details": "(f, amber)", "price": 120.00},
    {"name": "Ambre Vanillé", "details": "(f, amber)", "price": 125.00},
    {"name": "Ambre Oriental", "details": "(m, amber)", "price": 118.00},
    {"name": "Ambre Mystique", "details": "(m, amber)", "price": 135.00},
    {"name": "Ambre Solaire", "details": "(u, amber)", "price": 115.50},
    {"name": "Ambre Boisé", "details": "(u, amber)", "price": 145.00},
]


def print_client_support():
    global inventory, fake
    state = fake.state_abbr()

    # Select a random item (which is now a dictionary) from the inventory
    selected_item = fake.random_element(elements=inventory)

    client_support = {
        "txid": str(uuid.uuid4()),
        "rfid": hex(random.getrandbits(96)),
        "item": selected_item["name"],  # Extract the name from the dictionary
        "details": selected_item["details"],  # Extract the details from the dictionary
        "price": selected_item["price"],  # Extract the price from the dictionary
        "purchase_time": datetime.utcnow().isoformat(),
        "expiration_time": date(2025, 9, 29).isoformat(),  # Updated expiration date
        "days": fake.random_int(min=1, max=7),
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
