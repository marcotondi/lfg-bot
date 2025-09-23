# LFG Bot

![License](https://img.shields.io/github/license/marcotondi/lfg-bot?style=flat-square)
![Issues](https://img.shields.io/github/issues/marcotondi/lfg-bot?style=flat-square)

Un bot Telegram per organizzare sessioni di gioci di ruolo "Looking For Group" (LFG).

## Stato del Progetto

Questo progetto è **attivamente mantenuto** e in fase di sviluppo. Nuove funzionalità e miglioramenti vengono aggiunti regolarmente.

## Indice

- [Come Iniziare](#come-iniziare)
  - [Prerequisiti](#prerequisiti)
  - [Installazione](#installazione)
  - [Utilizzo](#utilizzo)
- [Documentazione](#documentazione)
- [Contribuire](#contribuire)
  - [Configurazione dell'ambiente di sviluppo](#configurazione-dellambiente-di-sviluppo)
  - [Struttura del Progetto](#struttura-del-progetto)
  - [Community](#community)
  - [Segnalazione Bug e Richieste di Aiuto](#segnalazione-bug-e-richieste-di-aiuto)
  - [Codice di Condotta](#codice-di-condotta)
  - [Versioning](#versioning)
- [Manutenzione](#manutenzione)
- [Licenza](#licenza)

## Come Iniziare

Queste istruzioni ti guideranno su come configurare ed eseguire il bot LFG sul tuo sistema locale.

### Prerequisiti

Assicurati di avere installato Python 3.8 o superiore.

### Installazione

1.  **Clona il repository:**
    ```bash
    git clone https://github.com/your-username/lfg-bot.git
    cd lfg-bot
    ```

2.  **Crea e attiva un ambiente virtuale (raccomandato):**
    ```bash
    python -m venv venv
    # Su Windows
    .\venv\Scripts\activate
    # Su macOS/Linux
    source venv/bin/activate
    ```

3.  **Installa le dipendenze:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configura il bot:**
    Copia il file `.env.example` e configuralo con il tuo token Telegram e altre impostazioni necessarie.

    ```properties
    # .env
    # Optional: Environment setting
    ENVIRONMENT=development

    # Telegram Bot Configuration
    TELEGRAM_TOKEN=xyz

    # Database Configuration
    DB_FILE=abc.db
    ```

### Utilizzo

Per avviare il bot, esegui:

```bash
python src/main.py
```

Oppure, se sei su Windows, puoi usare lo script `run_bot.bat`:

```bash
run_bot.bat
```

### Struttura del Progetto

```
lfg-bot/
├───src/
│   ├───config.py           # Configurazione del bot
│   ├───database.py         # Gestione del database
│   ├───main.py             # Punto di ingresso principale del bot
│   ├───handlers/           # Moduli per la gestione dei comandi e degli eventi
│   │   ├───admin/
│   │   ├─── .py            # Moduli per la gestione dei comandi per gli admin 
│   │   ├───common/
│   │   ├─── .py            # Moduli per la gestione dei comandi per gli utenti
│   │   ├───master/
│   │   ├─── .py            # Moduli per la gestione dei comandi per i master
│   │   │
│   ├───models/             # Definizioni dei modelli del database
│   │   ├───registration.py
│   │   ├───table.py
│   │   └───user.py
│   └───utils/              # Utilità e helper
│       └───decorators.py
├───requirements.txt        # Dipendenze Python
├───abc.db                  # Database SQLite (generato)
└───run_bot.bat             # Script per avviare il bot su Windows
```

### Segnalazione Bug

Per segnalare bug o richiedere nuove funzionalità, apri un'issue su GitHub: [GitHub Issues](https://github.com/marcotondi/lfg-bot/issues).

## Manutenzione

Questo progetto è mantenuto da:

-   [Marco](https://github.com/marcotondi/lfg-bot)

## Licenza

Questo progetto è distribuito sotto licenza `MIT License`. Vedi il file [LICENSE](LICENSE) per maggiori dettagli.
