from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    session,
    jsonify,
)
from flask_login import login_required
from database import collection_ordini, moduli_collection, societa_collection
from bson.objectid import ObjectId
from datetime import datetime
from utils import convert_objectid_to_str

moduli_bp = Blueprint("moduli", __name__)


def _normalize_progressivo(value):
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        digits = "".join(ch for ch in value if ch.isdigit())
        if digits:
            return int(digits)
    return None


def _get_next_progressivo(username):
    docs = list(
        moduli_collection.find(
            {"tipo": "sd1", "username": username, "progressivo": {"$exists": True}},
            {"progressivo": 1},
        )
    )
    progressivi = []
    for doc in docs:
        parsed = _normalize_progressivo(doc.get("progressivo"))
        if parsed is not None:
            progressivi.append(parsed)
    if not progressivi:
        return 1
    return max(progressivi) + 1


@moduli_bp.route("/ricerca_ordini", methods=["POST"])
@login_required
def ricerca_ordini():
    data = request.get_json()
    tipo = data.get("tipo_ricerca")
    username = session.get("username")
    query = {"username": username}
    if tipo == "numero" and data.get("numero"):
        query["numero"] = int(data.get("numero"))
    elif tipo == "data" and data.get("data_inizio") and data.get("data_fine"):
        i = datetime.strptime(data.get("data_inizio"), "%Y-%m-%d")
        f = datetime.strptime(data.get("data_fine"), "%Y-%m-%d").replace(
            hour=23, minute=59, second=59
        )
        query["data"] = {"$gte": i, "$lte": f}

    ordini = list(collection_ordini.find(query).sort("data", -1).limit(100))
    res = []
    for o in ordini:
        os = convert_objectid_to_str(o)
        os["timestamp"] = (
            o["data"].strftime("%Y-%m-%d %H:%M:%S") if "data" in o else "N/A"
        )
        os["dettagli"] = o.get("prodotti", [])
        res.append(os)
    return jsonify(success=True, ordini=res)


@moduli_bp.route("/api/ordini/<oid>")
@login_required
def get_ordine_details(oid):
    username = session.get("username")
    o = collection_ordini.find_one({"_id": ObjectId(oid), "username": username})
    if not o:
        return jsonify(success=False), 404
    os = convert_objectid_to_str(o)
    os["timestamp"] = o["data"].strftime("%Y-%m-%d %H:%M:%S")
    return jsonify(success=True, ordine=os)


@moduli_bp.route("/modulo_sd1")
@login_required
def modulo_sd1():
    return render_template("modulo_sd1_browser.html")


@moduli_bp.route("/modulo_sd1/nuovo")
@login_required
def nuovo_modulo_sd1():
    username = session.get("username")
    settings = societa_collection.find_one({"username": username}) or {}
    default_data = {
        "ragione_sociale": settings.get("ragione_sociale", ""),
        "sede_legale": settings.get("sede_legale", ""),
        "cap": settings.get("cap", ""),
        "comune": settings.get("comune", ""),
        "provincia": settings.get("provincia", ""),
        "partita_iva": settings.get("partita_iva", ""),
        "rappresentante_legale": settings.get("rappresentante_legale", ""),
        "codice_fiscale_rappresentante": settings.get("codice_fiscale_rappresentante", ""),
        "residenza_rappresentante": settings.get("residenza_rappresentante", ""),
        "comune_rappresentante": settings.get("comune_rappresentante", ""),
        "provincia_rappresentante": settings.get("provincia_rappresentante", ""),
        "impianto": settings.get("impianto", ""),
        "manifestazione_tipo": settings.get("manifestazione_tipo", ""),
        "manifestazione_incontro": settings.get("manifestazione_incontro", ""),
        "manifestazione_polisportiva": settings.get("manifestazione_polisportiva", ""),
    }
    return render_template(
        "modulo_sd1.html",
        modulo_id=None,
        view_only=False,
        default_data=default_data,
    )


@moduli_bp.route("/modulo_sd1/<mid>")
@login_required
def apri_modulo_sd1(mid):
    view_only = request.args.get("view") == "1"
    return render_template("modulo_sd1.html", modulo_id=mid, view_only=view_only)


@moduli_bp.route("/api/moduli/sd1/next-progressivo", methods=["GET"])
@login_required
def next_progressivo_sd1():
    username = session.get("username")
    return jsonify(success=True, progressivo=_get_next_progressivo(username))


@moduli_bp.route("/api/moduli/sd1", methods=["GET"])
@login_required
def lista_sd1():
    username = session.get("username")
    docs = list(
        moduli_collection.find({"tipo": "sd1", "username": username})
        .sort("data_creazione", -1)
        .limit(300)
    )

    items = []
    for d in docs:
        doc = convert_objectid_to_str(d)
        created = d.get("data_creazione")
        doc["data_creazione"] = (
            created.strftime("%Y-%m-%d %H:%M:%S") if isinstance(created, datetime) else ""
        )
        manif = d.get("manifestazione", {})
        doc["manifestazione_label"] = (
            f"{manif.get('giorno', '')}/{manif.get('mese', '')}/{manif.get('anno', '')}"
        ).strip("/")
        doc["societa_label"] = d.get("societa", {}).get("nome", "")
        items.append(doc)

    return jsonify(success=True, moduli=items)


@moduli_bp.route("/api/moduli/sd1/<mid>", methods=["GET"])
@login_required
def dettaglio_sd1(mid):
    username = session.get("username")
    try:
        oid = ObjectId(mid)
    except Exception:
        return jsonify(success=False, message="ID non valido"), 400

    doc = moduli_collection.find_one({"_id": oid, "tipo": "sd1", "username": username})
    if not doc:
        return jsonify(success=False, message="Modulo non trovato"), 404

    out = convert_objectid_to_str(doc)
    out.pop("data_creazione", None)
    return jsonify(success=True, modulo=out)


@moduli_bp.route("/api/moduli/sd1/<mid>", methods=["DELETE"])
@login_required
def elimina_sd1(mid):
    username = session.get("username")
    try:
        oid = ObjectId(mid)
    except Exception:
        return jsonify(success=False, message="ID non valido"), 400

    result = moduli_collection.delete_one({"_id": oid, "tipo": "sd1", "username": username})
    if result.deleted_count == 0:
        return jsonify(success=False, message="Modulo non trovato"), 404
    return jsonify(success=True)


@moduli_bp.route("/api/moduli/sd1", methods=["POST"])
@login_required
def salva_sd1():
    data = request.get_json() or {}
    username = session.get("username")
    modulo_id = data.pop("id", None)

    payload = {"tipo": "sd1", "username": username}
    payload.update(data)

    if modulo_id:
        try:
            oid = ObjectId(modulo_id)
        except Exception:
            return jsonify(success=False, message="ID non valido"), 400

        result = moduli_collection.update_one(
            {"_id": oid, "tipo": "sd1", "username": username},
            {"$set": payload},
        )
        if result.matched_count == 0:
            return jsonify(success=False, message="Modulo non trovato"), 404
        return jsonify(success=True, id=modulo_id, updated=True)

    next_progressivo = _get_next_progressivo(username)
    payload["progressivo"] = next_progressivo
    payload["data_creazione"] = datetime.now()
    ins = moduli_collection.insert_one(payload)
    return jsonify(success=True, id=str(ins.inserted_id), updated=False)


