# Tutorial progetto kiosk

## Primi passi

### Installare Visual Studio Code

Scarica Visual Studio Code da:
https://code.visualstudio.com/download?_exp_download=d53503e735

Scegli l'installer adatto al tuo sistema operativo. Se usi Windows, in genere va bene "User installer x64".

### Installare Python

Installa Python dal sito ufficiale:
https://www.python.org/downloads/

Python serve per avviare il backend, cioè i file con estensione `.py`.

### Installare MongoDB Compass

MongoDB Compass è utile per vedere il database in modo grafico, controllare i dati e modificarli senza usare solo il terminale.

### Installare GitHub Desktop

GitHub Desktop serve per collegare il progetto a GitHub e tenere una copia online del lavoro.

Download:
https://desktop.github.com/download/

Esempio del progetto online:
https://github.com/SylweKra/progetto_kiosk

## Avvio del progetto

1. Apri la cartella del progetto in VS Code con `File > Open Folder...`.
2. A sinistra troverai gli strumenti principali:
   - Esplora: file e cartelle.
   - Cerca: ricerca di file e parole all'interno dei file.
   - Controllo sorgente: gestione delle modifiche e collegamento con GitHub.
   - Esegui e debug: avvio e debug dei file `.py`.
   - Estensioni: installazione di Python, Python Debugger e altre estensioni utili.
3. Apri il terminale integrato di VS Code.
4. Installa le dipendenze con questo comando:

```bash
python -m pip install -r requirements.txt
```

5. Avvia il progetto con:

```bash
python app.py
```

6. Quando il backend è avviato, apri il link locale che compare nel terminale con `Ctrl + click`.

Se qualcosa non funziona, controlla prima il terminale, poi prova a reinstallare le dipendenze. Se serve, chiedimi aiuto.

## GitHub

GitHub è utile per salvare il progetto online e non perdere il lavoro.

Con GitHub Desktop puoi:

1. Aprire `File > Add local repository...`.
2. Selezionare la cartella del progetto.
3. Vedere le modifiche fatte in VS Code.
4. Fare commit e sincronizzare il progetto su GitHub.

## Database (MongoDB)

La configurazione del database si trova in [database.py](database.py).

Nel progetto è già presente una connessione a MongoDB Atlas. Se vuoi usare un database locale, puoi cambiare la connessione con quella su `localhost` indicata nel file.

Per usare un database online puoi configurare MongoDB Atlas:
https://www.mongodb.com/products/platform/atlas-database

## Pubblicazione online

Per mettere il progetto online in genere servono:

1. Un database su MongoDB Atlas.
2. Il progetto caricato su GitHub.
3. Un servizio di deploy come Render:
   https://render.com/

## Documentazione rapida del progetto

### File principali

- [app.py](app.py): avvia l'app Flask, registra i blueprint e gestisce la cartella di upload.
- [database.py](database.py): centralizza la connessione a MongoDB e le collection usate dal progetto.
- [utils.py](utils.py): funzioni di supporto, gestione delle sessioni guest e utilità per la serializzazione degli oggetti.
- [aggiungi.py](aggiungi.py): script di utilità per creare dati di esempio o fare test manuali sul database.
- [cleanup_script.py](cleanup_script.py): script che pulisce le sessioni scadute nel database.
- [requirements.txt](requirements.txt): elenco delle dipendenze Python necessarie per far partire il progetto.
- [tutorial.md](tutorial.md): questa guida di installazione e utilizzo.

### Cartella blueprints

Contiene i moduli Flask separati per area funzionale:

- [blueprints/admin.py](blueprints/admin.py): funzioni e route dell'area amministrativa.
- [blueprints/auth.py](blueprints/auth.py): login, autenticazione e gestione utenti.
- [blueprints/cameriere.py](blueprints/cameriere.py): area dedicata ai camerieri.
- [blueprints/cassa.py](blueprints/cassa.py): area cassa e gestione dei pagamenti.
- [blueprints/home.py](blueprints/home.py): pagina principale e routing iniziale.
- [blueprints/inventario.py](blueprints/inventario.py): gestione dell'inventario.
- [blueprints/moduli.py](blueprints/moduli.py): moduli e schermate operative collegate al progetto.
- [blueprints/stats.py](blueprints/stats.py): statistiche e riepiloghi.

### Cartella templates

Contiene i template HTML usati da Flask per renderizzare le pagine:

- [templates/base.html](templates/base.html): layout base comune a tutte le pagine.
- [templates/home.html](templates/home.html): homepage.
- [templates/login.html](templates/login.html): schermata di accesso.
- [templates/cassa.html](templates/cassa.html): interfaccia cassa.
- [templates/cameriere.html](templates/cameriere.html): interfaccia camerieri.
- [templates/inventario.html](templates/inventario.html): schermata inventario.
- [templates/impostazioni.html](templates/impostazioni.html): impostazioni del sistema.
- [templates/modulo_sd1.html](templates/modulo_sd1.html): modulo SD1.
- [templates/modulo_sd1_browser.html](templates/modulo_sd1_browser.html): versione browser del modulo SD1.
- [templates/ricevuta.html](templates/ricevuta.html): stampa o visualizzazione della ricevuta.
- [templates/statistiche.html](templates/statistiche.html): pagina statistiche.

### Cartella static

Contiene file statici caricati dal browser:

- [static/style.css](static/style.css): stile generale dell'app.
- [static/cassa.css](static/cassa.css): stile dedicato alla cassa.
- [static/image.png](static/image.png): immagine usata nel progetto.
- [static/logo-agenzia.png](static/logo-agenzia.png): logo dell'agenzia.
- [static/sfondo.png](static/sfondo.png): immagine di sfondo.
- [static/sfondousd.jpg](static/sfondousd.jpg): altro sfondo grafico.

### Cartella uploads

Contiene i file caricati o generati dall'applicazione durante l'uso.

### Nota finale

Se aggiungi nuovi file o cartelle, aggiorna questa sezione così la documentazione resta sempre allineata al progetto.
