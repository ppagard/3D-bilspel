# RetroFit – Användarhandledning

RetroFit är ett program för låne- och leasingberäkningar med amorteringsschema, sparande i databas och PDF-export.

## Starta programmet

Kör från projektets rotkatalog:

```bash
python -m retrofit.main
```

eller, om du står i `retrofit/`:

```bash
python main.py
```

## Fliken Beräkna

### Lån

1. Välj **Lån** i rullgardinen Typ.
2. Fyll i:
   - **Belopp (SEK)** – t.ex. 500 000
   - **Ränta (% per år)** – t.ex. 5,0
   - **Löptid (månader)** – t.ex. 60
3. Klicka **Beräkna**.

Du får månadsbetalning, totala beloppet och ett amorteringsschema (ruta + graf).

### Leasing

1. Välj **Leasing** i Typ.
2. Fyll i belopp, ränta, löptid samt **Residualvärde (SEK)** – det förväntade värdet i slutet av avtalet.
3. Klicka **Beräkna**.

### Knappar

- **Beräkna** – uppdaterar resultat och graf.
- **Spara till databas** – sparar den senaste beräkningen. Aktiveras efter en beräkning.
- **Exportera till PDF** – sparar en rapport med beräkningsdata och amorteringsschema som PDF. Aktiveras efter en beräkning.

## Fliken Historik

- **Uppdatera** – hämtar alla sparade beräkningar från databasen.
- **Ladda** – välj en rad, klicka **Ladda**. Beräkningen fylls i på fliken Beräkna och räknas om så att schema och graf visas.
- **Radera** – välj en rad, klicka **Radera** och bekräfta. Beräkningen tas bort från databasen.

Listan uppdateras automatiskt när du byter till fliken Historik.

## Konfiguration

`config.json` i `retrofit/` styr t.ex.:

- `default_currency` – valuta (standard: SEK)
- `decimal_places` – antal decimaler
- `use_swedish_format` – svenskt talformat

## Databas

Sparade beräkningar ligger i `retrofit/data/finance.db` (SQLite). Filen skapas vid första sparningen.

## Krav

- Python 3.8+
- PyQt5, fpdf2, matplotlib

Installation:

```bash
pip install PyQt5 fpdf2 matplotlib
```

(sqlite3 ingår i Python.)
