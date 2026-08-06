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
from database import collection_ordini, guest_sessions_collection
from utils import get_or_create_guest_session, convert_objectid_to_str

cameriere_bp = Blueprint("cameriere", __name__)


@cameriere_bp.route("/login_cameriere")
def login_cameriere():
    gid = get_or_create_guest_session()
    session["role"] = "cameriere"
    session["username"] = f"guest_{gid[:8]}"
    return redirect(url_for("cameriere.cameriere_root"))


@cameriere_bp.route("/cameriere", methods=["GET", "POST"])
def cameriere_root():
    if session.get("role") != "cameriere":
        return redirect(url_for("auth.login"))
    gid = get_or_create_guest_session()
    gs = guest_sessions_collection.find_one({"guest_id": gid})
    if not gs:
        return redirect(url_for("auth.login"))

    ordini_trovati = gs.get("ordini_trovati", [])
    if request.method == "POST" and "query" in request.form:
        q = request.form.get("query")
        if q:
            try:
                num = int(q)
                nuovi = list(collection_ordini.find({"numero": num}))
                for o in nuovi:
                    if str(o["_id"]) not in [x["_id"] for x in ordini_trovati]:
                        os = convert_objectid_to_str(o)
                        os["dettagli"] = o.get("prodotti", [])
                        ordini_trovati.append(os)
                guest_sessions_collection.update_one(
                    {"guest_id": gid}, {"$set": {"ordini_trovati": ordini_trovati}}
                )
            except ValueError:
                flash("Numero non valido", "error")
    return render_template(
        "cameriere.html",
        ordini=ordini_trovati,
        ricerca_effettuata=bool(ordini_trovati),
        username=session.get("username"),
    )


@cameriere_bp.route("/nascondi_ordine/<oid>", methods=["POST"])
def nascondi_ordine(oid):
    gid = session.get("guest_id")
    if gid:
        gs = guest_sessions_collection.find_one({"guest_id": gid})
        if gs:
            list_o = [o for o in gs.get("ordini_trovati", []) if o["_id"] != oid]
            guest_sessions_collection.update_one(
                {"guest_id": gid}, {"$set": {"ordini_trovati": list_o}}
            )
    return redirect(url_for("cameriere.cameriere_root"))


@cameriere_bp.route("/pulisci_lista", methods=["POST"])
def pulisci_lista():
    gid = session.get("guest_id")
    if gid:
        guest_sessions_collection.update_one(
            {"guest_id": gid}, {"$set": {"ordini_trovati": []}}
        )
    return redirect(url_for("cameriere.cameriere_root"))
