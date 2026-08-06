# ESEGUI UNA VOLTA per creare utenti
from pymongo import MongoClient
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
client = MongoClient("mongodb://localhost:27017/")
db = client['kioskdb']
# Collection ordini
ordini_collection = db['ordini']

ordine_di_esempio = {
    "numero": 4,
    "dettagli": [
        {"prodotto": "Pizza Margherita", "quantità": 2},
        {"prodotto": "Acqua Naturale", "quantità": 1},
        {"prodotto": "Birra Media", "quantità": 1}
    ]
}

YXurYbR4axLbBVeY