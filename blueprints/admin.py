from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from flask_login import login_required
from database import users_collection, societa_collection, registro_collection
from flask_bcrypt import Bcrypt

admin_bp = Blueprint("admin", __name__)
bcrypt = Bcrypt()


@admin_bp.route("/impostazioni", methods=["GET", "POST"])
@login_required
def impostazioni():
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))
    msg = None
    if request.method == "POST":
        u, p, r = (
            request.form["username"],
            request.form["password"],
            request.form["role"],
        )
        if users_collection.find_one({"username": u}):
            msg = "Esiste già"
        else:
            users_collection.insert_one(
                {
                    "username": u,
                    "password": bcrypt.generate_password_hash(p).decode("utf-8"),
                    "role": r,
                }
            )
            msg = f"Creato {u}"
    return render_template(
        "impostazioni.html",
        message=msg,
        dati=societa_collection.find_one({"username": session.get("username")}) or {},
    )


@admin_bp.route("/impostazioni_societa", methods=["GET", "POST"])
@login_required
def impostazioni_societa():
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))
    username = session.get("username")
    if request.method == "POST":
        upd = {
            k: request.form.get(k, "").strip()
            for k in [
                "ragione_sociale",
                "indirizzo",
                "sede_legale",
                "cap",
                "comune",
                "provincia",
                "partita_iva",
                "telefono",
                "messaggio_scontrino",
                "rappresentante_legale",
                "codice_fiscale_rappresentante",
                "residenza_rappresentante",
                "comune_rappresentante",
                "provincia_rappresentante",
                "impianto",
                "manifestazione_tipo",
                "manifestazione_incontro",
                "manifestazione_polisportiva",
            ]
        }
        upd["azzera_ordini_chiusura"] = (
            "1" if request.form.get("azzera_ordini_chiusura") else "0"
        )
        upd["username"] = username
        societa_collection.update_one(
            {"username": username}, {"$set": upd}, upsert=True
        )
        flash("Dati società salvati correttamente", "success-message")
    return redirect(url_for("admin.impostazioni"))


@admin_bp.route("/registro_corrispettivi")
@login_required
def registro_corrispettivi():
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))
    username = session.get("username")
    reg = list(registro_collection.find({"username": username}).sort("data", -1))
    for r in reg:
        r["totale_lordo"] = float(r.get("totale_lordo", 0))
        r["contanti"] = float(r.get("contanti", 0))
        r["pos"] = float(r.get("pos", 0))
        r["totale_iva"] = float(r.get("totale_iva", 0))
        r["numero_scontrini"] = int(r.get("numero_scontrini", 0))
    return render_template("registro_corrispettivi.html", registro=reg)
