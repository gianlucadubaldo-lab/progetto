from flask import Blueprint, render_template, session, redirect, url_for
from flask_login import login_required
from database import collection_ordini, calendario_collection
from datetime import datetime, timedelta

stats_bp = Blueprint("stats", __name__)


@stats_bp.route("/statistiche")
@login_required
def statistiche():
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))
    username = session.get("username")
    fine = datetime.now()
    inizio = fine - timedelta(days=30)
    ordini = list(
        collection_ordini.find(
            {"data": {"$gte": inizio, "$lte": fine}, "username": username}
        )
    )

    if not ordini:
        return render_template(
            "statistiche.html",
            totale_incasso=0.0,
            totale_ordini=0,
            media_ordine=0.0,
            giorni_labels=[],
            incassi_values=[],
            prodotti_labels=[],
            prodotti_values=[],
            orari_labels=list(range(24)),
            orari_values=[0] * 24,
            partite_spettatori=[],
        )

    totale = sum(float(o.get("totale", 0)) for o in ordini)
    inc_giorno = {}
    prod_freq = {}
    hours = [0] * 24
    for o in ordini:
        d = o["data"]
        inc_giorno[d.strftime("%Y-%m-%d")] = inc_giorno.get(
            d.strftime("%Y-%m-%d"), 0
        ) + float(o.get("totale", 0))
        hours[d.hour] += 1
        for p in o.get("prodotti", []):
            prod_freq[p["nome"]] = prod_freq.get(p["nome"], 0) + int(
                p.get("quantita", 0)
            )

    top_p = sorted(prod_freq.items(), key=lambda x: x[1], reverse=True)[:10]

    partite = list(calendario_collection.find().sort("data", 1))
    ps = []
    for p in partite:
        is_casa = "semproniano" in p["casa"].lower()
        spett = 0
        if is_casa:
            o_g = collection_ordini.find(
                {
                    "data": {
                        "$gte": p["data"].replace(hour=0, minute=0, second=0),
                        "$lt": p["data"].replace(hour=23, minute=59, second=59),
                    },
                    "username": username,
                }
            )
            for o in o_g:
                for prod in o.get("prodotti", []):
                    if "biglietto" in prod["nome"].lower():
                        spett += int(prod["quantita"])
        ps.append(
            {
                "data": p["data"].strftime("%d/%m/%Y"),
                "casa": p["casa"],
                "ospite": p["ospite"],
                "risultato": p.get("risultato", ""),
                "spettatori": spett,
                "is_casa": is_casa,
            }
        )

    return render_template(
        "statistiche.html",
        totale_incasso=round(totale, 2),
        totale_ordini=len(ordini),
        media_ordine=round(totale / len(ordini), 2),
        giorni_labels=sorted(inc_giorno.keys()),
        incassi_values=[round(inc_giorno[g], 2) for g in sorted(inc_giorno.keys())],
        prodotti_labels=[x[0] for x in top_p],
        prodotti_values=[x[1] for x in top_p],
        orari_labels=list(range(24)),
        orari_values=hours,
        partite_spettatori=ps,
    )
