from flask import Blueprint, render_template, redirect, url_for, session, jsonify
from flask_login import login_required
from database import calendario_collection, db
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from bs4 import BeautifulSoup
import time
import re

home_bp = Blueprint("home", __name__)


def aggiorna_calendario_semproniano(username):
    """Scrapa il calendario del Semproniano da tuttocampo.it usando Selenium"""
    url = "https://www.tuttocampo.it/Toscana/TerzaCategoria/GironeAGrosseto/Squadra/Semproniano/1099692/Calendario"

    driver = None
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        driver = webdriver.Chrome(options=options)
        driver.get(url)

        wait = WebDriverWait(driver, 10)
        team_calendar = wait.until(
            EC.presence_of_element_located((By.ID, "team_calendar"))
        )
        time.sleep(3)

        html = driver.page_source
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")

        partite = []
        team_calendar_div = soup.find("div", {"id": "team_calendar"})
        if not team_calendar_div:
            return

        tabella = team_calendar_div.find("table")
        if not tabella:
            return

        righe = tabella.find_all("tr")
        pattern_data = r"(\d{1,2})/(\d{1,2})"
        pattern_numero = r"^\d+$"

        for idx, riga in enumerate(righe):
            celle = riga.find_all("td")
            if len(celle) < 3:
                continue

            try:
                testo_casa_raw = celle[1].text.strip()
                testo_ospite_raw = celle[2].text.strip()

                linee_casa = [
                    l.strip() for l in testo_casa_raw.split("\n") if l.strip()
                ]
                linee_ospite = [
                    l.strip() for l in testo_ospite_raw.split("\n") if l.strip()
                ]

                if len(linee_casa) < 1 or len(linee_ospite) < 1:
                    continue

                casa = next(
                    (
                        l
                        for l in linee_casa
                        if not re.match(pattern_numero, l)
                        and "ritirata" not in l.lower()
                    ),
                    None,
                )
                ospite = next(
                    (
                        l
                        for l in reversed(linee_ospite)
                        if not re.match(pattern_numero, l)
                        and "ritirata" not in l.lower()
                    ),
                    None,
                )

                punteggio_casa = "-"
                punteggio_ospite = "-"

                # Semplificazione logica punteggio
                for l in linee_casa:
                    if re.match(r"^[\d\s\-]+$", l.strip()) and not re.search(
                        pattern_data, l
                    ):
                        punteggio_casa = l.strip()
                        break
                    elif "ritirata" in l.lower():
                        punteggio_casa = "RITIRATA"
                        break

                for l in linee_ospite:
                    if re.match(r"^[\d\s\-]+$", l.strip()) and not re.search(
                        pattern_data, l
                    ):
                        punteggio_ospite = l.strip()
                        break
                    elif "ritirata" in l.lower():
                        punteggio_ospite = "RITIRATA"
                        break

                risultato = f"{punteggio_casa} - {punteggio_ospite}"
                data_str = next(
                    (
                        l
                        for l in linee_casa + linee_ospite
                        if re.search(pattern_data, l)
                    ),
                    None,
                )

                if not casa or not ospite:
                    continue

                data_obj = datetime(2099, 12, 31)
                if data_str:
                    match = re.search(r"(\d{1,2})/(\d{1,2})", data_str)
                    if match:
                        giorno, mese = int(match.group(1)), int(match.group(2))
                        anno = 2025 if mese < 8 else 2024
                        data_obj = datetime.strptime(
                            f"{giorno:02d}/{mese:02d}/{anno}", "%d/%m/%Y"
                        )

                partite.append(
                    {
                        "data": data_obj,
                        "casa": casa,
                        "ospite": ospite,
                        "risultato": risultato,
                        "timestamp": datetime.now(),
                        "username": username,
                    }
                )
            except Exception:
                continue

        if partite:
            calendario_collection.delete_many({"username": username})
            calendario_collection.insert_many(partite)

        driver.quit()
    except Exception:
        if driver:
            driver.quit()


@home_bp.route("/")
def index():
    return redirect(url_for("auth.login"))


@home_bp.route("/home")
@login_required
def home():
    if session.get("role") != "admin":
        return redirect(url_for("auth.login"))
    username = session.get("username")
    partite = list(calendario_collection.find({"username": username}).sort("data", 1))
    return render_template("home.html", partite=partite)


@home_bp.route("/aggiorna_calendario", methods=["POST"])
@login_required
def aggiorna_calendario():
    if session.get("role") != "admin":
        return jsonify(success=False, message="Non autorizzato")
    username = session.get("username")
    try:
        aggiorna_calendario_semproniano(username)
        return jsonify(success=True, message="Calendario aggiornato con successo")
    except Exception as e:
        return jsonify(success=False, message=f"Errore: {str(e)}")
