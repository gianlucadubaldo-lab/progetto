"""
Modulo di configurazione del database MongoDB
Centralizza tutte le connessioni e le collections
"""

from pymongo import MongoClient

# Connessione a MongoDB
client = MongoClient("mongodb+srv://gianlucadubaldo_db_user:7cTJeuclbojaVjHo@ginaluca.ovewjhs.mongodb.net/")
# Alternativa per localhost:
# client = MongoClient("mongodb://localhost:27017")

db = client['kioskdb']

# Collections
users_collection = db['users']
collection_ordini = db['ordini']
guest_sessions_collection = db['guest_sessions']
societa_collection = db['dati_societa']
registro_collection = db['registro_corrispettivi']
calendario_collection = db['calendario_semproniano']
inventario_collection = db['inventario']
categorie_collection = db['categorie']
moduli_collection = db['moduli']
