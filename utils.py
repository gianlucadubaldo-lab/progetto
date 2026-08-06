import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from flask import session
from bson.objectid import ObjectId
from database import guest_sessions_collection

def convert_objectid_to_str(ordine):
    """Converte ObjectId in stringa per la serializzazione JSON"""
    if not ordine:
        return None
    ordine_copy = ordine.copy()
    if '_id' in ordine_copy:
        ordine_copy['_id'] = str(ordine_copy['_id'])
    return ordine_copy

def cleanup_expired_sessions():
    """Rimuove le sessioni scadute (più vecchie di 24 ore)"""
    expiry_time = datetime.now() - timedelta(hours=24)
    guest_sessions_collection.delete_many({
        'created_at': {'$lt': expiry_time}
    })

def get_or_create_guest_session():
    """Ottiene o crea una sessione guest unica"""
    cleanup_expired_sessions()
    
    # Se l'utente ha già un guest_id nella sessione, verificalo
    if 'guest_id' in session:
        existing_session = guest_sessions_collection.find_one({
            'guest_id': session['guest_id'],
            'created_at': {'$gte': datetime.now() - timedelta(hours=24)}
        })
        if existing_session:
            return session['guest_id']
    
    # Crea una nuova sessione guest
    guest_id = str(uuid.uuid4())
    guest_sessions_collection.insert_one({
        'guest_id': guest_id,
        'created_at': datetime.now(),
        'ordini_trovati': []
    })
    session['guest_id'] = guest_id
    return guest_id

def _rome_day_bounds(now=None):
    tz = ZoneInfo('Europe/Rome')
    # Assicurati che now sia offset-aware se fornito, altrimenti usa l'ora corrente aware
    if now is None:
        now = datetime.now(tz)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=tz)
    else:
        now = now.astimezone(tz)
        
    start_local = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = start_local + timedelta(days=1)
    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)
    day_key = start_local.date().isoformat()
    return start_utc, end_utc, day_key
