# Projektplan: Python GUI för låne- och leasingberäkningar

## Mål
Skapa ett avancerat Python GUI-program som beräknar återbetalningsplaner för både lån och leasing, med stöd för databassparning, grafik och PDF-export.

## Krav från användaren
- GUI (inte CLI)
- Stöd för både lån och leasing
- Spara resultat till lokal SQLite-databas
- Avancerat gränssnitt med grafik och PDF-export

## Tekniska val
- **GUI**: PyQt5 (för bättre stöd för avancerade funktioner)
- **Databas**: SQLite (inbyggd i Python, enkel hantering)
- **Grafik**: matplotlib (för amorteringsschema)
- **PDF-export**: fpdf2 (enkel, lätt att använda)

## Projektstruktur
```
retrofit/
├── main.py                  # Huvudprogrammet (startpunkt)
├── database.py              # Databasanslutning och CRUD-funktioner
├── calculator.py            # Beräkningslogik (lån & leasing)
├── gui.py                   # GUI-fönster, inmatningsfält, knappar
├── report.py                # PDF-export och rapportgenerering
├── config.json              # Konfigurationsfil (t.ex. standardinställningar)
├── data/
│   └── finance.db           # Skapas automatiskt
├── docs/
│   └── README.md            # Användarhandledning
└── examples/
    └── sample_calculations.json  # Exempelfiler
```

## Föreslagna funktioner per modul

### `database.py`
- Skapa och ansluta till SQLite-databas
- Tabell: `loans` (id, type, amount, rate, term, payment, start_date, end_date)
- Funktioner: `save_calculation()`, `get_all_calculations()`, `delete_calculation(id)`

### `calculator.py`
- Funktion: `calculate_loan(principal, rate, term_months)`
- Funktion: `calculate_lease(lease_amount, rate, term_months, residual_value)`
- Returnerar: amorteringsschema (lista med månadsbetalningar, ränta, principalkomponent)

### `gui.py`
- Huvudfönster med:
  - Val av typ: Lån / Leasing
  - Inmatningsfält (belopp, ränta, löptid)
  - Knapp: "Beräkna"
  - Visning av resultat (total, månadsbelopp)
  - Grafikfält (matplotlib-plot för amorteringsschema)
  - Knapp: "Spara till databas"
  - Knapp: "Exportera till PDF"

### `report.py`
- Skapa PDF med fpdf2
- Innehåller: beräkningsdata, grafik (amorteringsschema), datum

### `config.json`
```json
{
  "default_currency": "SEK",
  "decimal_places": 2,
  "use_swedish_format": true
}
```

## Testplan
- Testa olika lånebelopp, räntor och löptider
- Kontrollera att data sparas korrekt i databasen
- Testa PDF-export med olika resultat
- Kontrollera att grafiken visas korrekt

## Dokumentation
- Skapa en README med användarhandledning
- Lägg till kommentarer i koden
- Skapa en exempelfil med typiska beräkningar

## Kommandon för utveckling
- Installera krav: `pip install PyQt5 fpdf2 matplotlib sqlite3`
- Kör programmet: `python main.py`

## Nästa steg
När användaren säger "OK, bygg det nu", kommer jag att:
1. Skapa alla filer med korrekt innehåll
2. Implementera varje komponent steg för steg
3. Testa funktionerna
4. Säkerställa att allt fungerar tillsammans