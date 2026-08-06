from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    session,
    flash,
    jsonify,
)
from flask_login import login_required
from database import collection_ordini, inventario_collection
from bson.objectid import ObjectId
from datetime import datetime

cassa_bp = Blueprint("cassa", __name__)


@cassa_bp.route("/cassa")
@login_required
def cassa_root():
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))
    username = session.get("username")
    prodotti = inventario_collection.find({"username": username})
    categorizzati = {}
    for p in prodotti:
        cat = p.get("categoria", "Altro")
        categorizzati.setdefault(cat, []).append(
            {
                "_id": str(p["_id"]),
                "nome": p["nome"],
                "prezzo": float(p["prezzo"]),
                "quantita": int(p.get("quantita", 0)),
            }
        )
    return render_template("cassa.html", prodotti_categorizzati=categorizzati)


@cassa_bp.route("/conferma_pagamento", methods=["POST"])
@login_required
def conferma_pagamento():
    dati = request.get_json()
    prodotti = dati.get("prodotti", [])
    totale_ricevuto = round(float(dati.get("totale", 0)), 2)
    pagato = round(float(dati.get("pagato", 0)), 2)
    metodo = (dati.get("metodoPagamento") or "pos").strip().lower()

    if not prodotti:
        return jsonify(success=False, message="Carrello vuoto")

    username = session.get("username")
    dettagli = []
    totale_calcolato = 0.0
    for item in prodotti:
        p_db = inventario_collection.find_one(
            {"_id": ObjectId(item["_id"]), "username": username}
        )
        if not p_db:
            continue
        qta = int(item.get("quantita", 0))
        if qta > int(p_db.get("quantita", 0)):
            return jsonify(
                success=False, message=f"Scorta insufficiente per {p_db['nome']}"
            )
        prezzo = float(p_db["prezzo"])
        totale_calcolato += prezzo * qta
        dettagli.append(
            {
                "id": str(p_db["_id"]),
                "nome": p_db["nome"],
                "categoria": p_db.get("categoria"),
                "quantita": qta,
                "prezzo": prezzo,
                "totale": round(prezzo * qta, 2),
            }
        )

    if abs(totale_ricevuto - totale_calcolato) > 0.01:
        return jsonify(success=False, message="Errore totale")

    for item in dettagli:
        inventario_collection.update_one(
            {"_id": ObjectId(item["id"]), "username": username},
            {"$inc": {"quantita": -item["quantita"]}},
        )

    from database import societa_collection

    societa = societa_collection.find_one({"username": username})
    azzera_ordini = False
    last_chiusura = None
    if societa:
        azzera_ordini = societa.get("azzera_ordini_chiusura") == "1"
        last_chiusura = societa.get("last_chiusura_time")

    if azzera_ordini and last_chiusura:
        ultimo = collection_ordini.find_one(
            {"username": username, "data": {"$gt": last_chiusura}},
            sort=[("numero", -1)],
        )
    else:
        ultimo = collection_ordini.find_one(
            {"username": username}, sort=[("numero", -1)]
        )

    numero = (int(ultimo["numero"]) + 1) if ultimo and "numero" in ultimo else 0

    is_contanti = metodo in ("contanti", "cash", "cassa")
    ordine = {
        "numero": numero,
        "data": datetime.now(),
        "prodotti": dettagli,
        "totale": totale_calcolato,
        "pagato": pagato,
        "resto": round(pagato - totale_calcolato, 2),
        "nota": dati.get("nota"),
        "metodo_pagamento": "contanti" if is_contanti else "pos",
        "pagamento_pos": not is_contanti,
        "pagamento_contanti": is_contanti,
        "username": username,
    }
    oid = collection_ordini.insert_one(ordine).inserted_id
    return jsonify(success=True, ordine_id=str(oid))


@cassa_bp.route("/ricevuta/<ordine_id>")
@login_required
def ricevuta(ordine_id):
    username = session.get("username")
    ordine = collection_ordini.find_one(
        {"_id": ObjectId(ordine_id), "username": username}
    )
    if not ordine:
        return "Non trovato", 404
    ordine["data_str"] = ordine["data"].strftime("%d/%m/%Y")
    ordine["ora_str"] = ordine["data"].strftime("%H:%M")
    return render_template("ricevuta.html", ordine=ordine)


@cassa_bp.route("/verifica_disponibilita", methods=["POST"])
@login_required
def verifica_disponibilita():
    data = request.get_json()
    username = session.get("username")
    p = inventario_collection.find_one(
        {"_id": ObjectId(data.get("_id")), "username": username}
    )
    if not p:
        return jsonify(success=False, message="Non trovato")
    scorta = int(p.get("quantita", 0))
    qta = int(data.get("quantita", 0))
    if qta > scorta:
        return jsonify(success=False, message=f"Disponibili {scorta}")
    return jsonify(success=True)
