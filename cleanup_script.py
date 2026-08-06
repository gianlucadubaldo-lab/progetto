from pymongo import MongoClient
from datetime import datetime, timedelta
import schedule
import time

# MongoDB config
client = MongoClient("mongodb://localhost:27017/")
db = client['kioskdb']
guest_sessions_collection = db['guest_sessions']

def cleanup_expired_sessions():
    """Rimuove le sessioni scadute (più vecchie di 24 ore)"""
    expiry_time = datetime.now() - timedelta(hours=24)
    result = guest_sessions_collection.delete_many({
        'created_at': {'$lt': expiry_time}
    })
    print(f"Rimosse {result.deleted_count} sessioni scadute")

# Programma la pulizia ogni ora
schedule.every().hour.do(cleanup_expired_sessions)

if __name__ == "__main__":
    print("Script di pulizia avviato...")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Controlla ogni minuto
