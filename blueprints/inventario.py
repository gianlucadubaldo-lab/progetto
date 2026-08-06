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
from database import db, inventario_collection, registro_collection, collection_ordini
from utils import convert_objectid_to_str, _rome_day_bounds
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
from datetime import datetime
import os
import pandas as pd

inventario_bp = Blueprint("inventario", __name__)


@inventario_bp.route("/inventario", methods=["GET", "POST"])
@login_required
def inventario_root():
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        file = request.files.get("file")
        if file and file.filename.endswith(".xlsx"):
            from flask import current_app

            filename = secure_filename(file.filename)
            filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)
            try:
                username = session.get("username")
                df = pd.read_excel(filepath)
                if {"nome", "prezzo", "quantita", "categoria"}.issubset(df.columns):
                    data = df.to_dict(orient="records")
                    for r in data:
                        nome = str(r.get("nome", "")).strip()
                        categoria = str(r.get("categoria", "Altro")).strip() or "Altro"
                        prezzo = float(r.get("prezzo", 0) or 0)
                        qta = int(r.get("quantita", 0) or 0)
                        if nome:
                            inventario_collection.update_one(
                                {
                                    "nome": nome,
                                    "categoria": categoria,
                                    "username": username,
                                },
                                {
                                    "$set": {"prezzo": prezzo},
                                    "$setOnInsert": {
                                        "quantita": qta,
                                        "username": username,
                                    },
                                },
                                upsert=True,
                            )
                    flash("Import da Excel completato.", "success-message")
                else:
                    flash("Colonne Excel mancanti.", "error")
            except Exception as e:
                flash(f"Errore import: {e}", "error")

    username = session.get("username")
    items = list(inventario_collection.find({"username": username}).sort("nome", 1))
    inventario_list = [
        {
            "_id": str(i.get("_id")),
            "nome": i.get("nome", ""),
            "categoria": i.get("categoria", "Altro"),
            "prezzo": float(i.get("prezzo", 0) or 0),
            "quantita": int(i.get("quantita", 0) or 0),
        }
        for i in items
    ]

    registro = list(
        registro_collection.find({"username": username}).sort("data", -1).limit(365)
    )
    for r in registro:
        r["totale_lordo"] = float(r.get("totale_lordo", 0))
        r["contanti"] = float(r.get("contanti", 0))
        r["pos"] = float(r.get("pos", 0))
        r["totale_iva"] = float(r.get("totale_iva", 0))
        r["numero_scontrini"] = int(r.get("numero_scontrini", 0))

    months = {}
    for r in registro:
        d = r.get("data")
        month_key = r.get(
            "day_key", d.strftime("%Y-%m") if isinstance(d, datetime) else str(d)
        )[:7]
        agg = months.setdefault(
            month_key,
            {
                "mese": month_key,
                "totale_lordo": 0.0,
                "contanti": 0.0,
                "pos": 0.0,
                "totale_iva": 0.0,
                "numero_scontrini": 0,
            },
        )
        agg["totale_lordo"] += r["totale_lordo"]
        agg["contanti"] += r["contanti"]
        agg["pos"] += r["pos"]
        agg["totale_iva"] += r["totale_iva"]
        agg["numero_scontrini"] += r["numero_scontrini"]

    riepilogo_mesi = sorted(months.values(), key=lambda x: x["mese"], reverse=True)
    mese_selected = request.args.get("mese", "").strip()
    mese_totali = months.get(mese_selected) if mese_selected else None

    return render_template(
        "inventario.html",
        inventario=inventario_list,
        registro=registro,
        riepilogo_mesi=riepilogo_mesi,
        mese_selected=mese_selected,
        mese_totali=mese_totali,
    )


@inventario_bp.route("/aggiorna_prodotto", methods=["POST"])
@login_required
def aggiorna_prodotto():
    if session.get("role") != "admin":
        return jsonify(success=False, message="Non autorizzato")
    data = request.get_json()
    username = session.get("username")
    try:
        prodotto_id = ObjectId(data.get("id"))
        nome, categoria = (
            data.get("nome", "").strip(),
            data.get("categoria", "").strip(),
        )
        if not nome or not categoria:
            return jsonify(success=False, message="Campi vuoti")
        prezzo = round(float(str(data.get("prezzo")).replace(",", ".")), 2)
        quantità = int(float(str(data.get("quantità")).replace(",", ".")))
        inventario_collection.update_one(
            {"_id": prodotto_id, "username": username},
            {
                "$set": {
                    "nome": nome,
                    "prezzo": prezzo,
                    "quantita": quantità,
                    "categoria": categoria,
                }
            },
        )
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e))


@inventario_bp.route("/aggiungi_prodotto", methods=["POST"])
@login_required
def aggiungi_prodotto():
    if session.get("role") != "admin":
        return jsonify(success=False, message="Non autorizzato")
    data = request.get_json()
    username = session.get("username")
    try:
        nome, categoria = (
            data.get("nome", "").strip(),
            data.get("categoria", "").strip(),
        )
        if not nome or not categoria:
            return jsonify(success=False, message="Campi vuoti")
        prezzo = round(float(str(data.get("prezzo")).replace(",", ".")), 2)
        quantita = int(float(str(data.get("quantità")).replace(",", ".")))
        if inventario_collection.find_one({"nome": nome, "username": username}):
            return jsonify(success=False, message="Esiste già")
        inventario_collection.insert_one(
            {
                "nome": nome,
                "prezzo": prezzo,
                "quantita": quantita,
                "categoria": categoria,
                "username": username,
            }
        )
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e))


@inventario_bp.route("/elimina_prodotto", methods=["POST"])
@login_required
def elimina_prodotto():
    if session.get("role") != "admin":
        return jsonify(success=False, message="Non autorizzato")
    data = request.get_json()
    username = session.get("username")
    try:
        inventario_collection.delete_one(
            {"_id": ObjectId(data.get("id")), "username": username}
        )
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e))


@inventario_bp.route("/esegui_chiusura", methods=["POST"])
@login_required
def esegui_chiusura():
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))
    start_utc, end_utc, day_key = _rome_day_bounds()
    username = session.get("username")
    ordini_giorno = list(
        collection_ordini.find(
            {"data": {"$gte": start_utc, "$lt": end_utc}, "username": username}
        )
    )
    totale = totale_iva = contanti = pos = 0.0
    for o in ordini_giorno:
        tot = float(o.get("totale", 0) or 0)
        totale += tot
        totale_iva += float(o.get("totale_iva", 0) or 0)
        if o.get("pagamento_contanti", False):
            contanti += tot
        elif o.get("pagamento_pos", False):
            pos += tot
        else:
            metodo = str(o.get("metodo_pagamento", "pos")).lower()
            if metodo in ("contanti", "cash", "cassa"):
                contanti += tot
            else:
                pos += tot
    registro_doc = {
        "data": datetime.fromisoformat(day_key + "T00:00:00+00:00"),
        "day_key": day_key,
        "totale_lordo": round(totale, 2),
        "contanti": round(contanti, 2),
        "pos": round(pos, 2),
        "totale_iva": round(totale_iva, 2),
        "numero_scontrini": len(ordini_giorno),
        "username": username,
    }
    registro_collection.update_one(
        {"day_key": day_key, "username": username}, {"$set": registro_doc}, upsert=True
    )
    from database import societa_collection

    societa_collection.update_one(
        {"username": username}, {"$set": {"last_chiusura_time": datetime.now()}}
    )
    flash("Chiusura registrata", "success-message")
    return redirect(url_for("inventario.inventario_root"))
