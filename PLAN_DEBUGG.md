# Debugg‑plan för RetroFit‑programmet

## Översikt
Denna fil beskriver en detaljerad felsöknings- och testplan för hela programmet (`main.py`, `gui.py` och `calculator.py`). Målet är att identifiera potentiella buggar, edge‑cases samt förbättringsområden och verifiera korrekt funktion genom systematiska tester.

---

## 1️⃣ Huvudprogram (`main.py`)
| Kontrollpunkt | Vad att titta på |
|---------------|------------------|
| Import av `LoanCalculatorGUI` | Säkerställ att modul‑namnet och sökvägen stämmer (filen finns i samma paket). |
| `if __name__ == "__main__"` | Inga oväntade sidoeffekter vid import. |
| Avslutning med `sys.exit(app.exec_())` | På macOS kan `exec_()` ge varningsmeddelanden i nyare PyQt‑versioner – verifiera att programmet startar utan fel. |

**Test:** Kör `python -m retrofit.main` och bekräfta att inget undantag kastas innan GUI visas.

---

## 2️⃣ Kalkylatormodulen (`calculator.py`)
### 2.1 Allmänna strukturella frågor
- Typ‑annoteringar är breda (`Dict[str, object]`). Kan ersättas med `TypedDict` för tydligare nycklar.
- Endast `datetime` importeras – används för datumformat.

### 2.2 `calculate_loan`
| Potentiell bug / edge case | Beskrivning |
|----------------------------|-------------|
| **Division med noll** (`term_months == 0`) | Om både `rate == 0` *och* `term_months == 0` blir en `ZeroDivisionError`. |
| **Negativ ränta** | Inga kontroller – negativa räntor ger negativ `monthly_rate`, vilket kan leda till oväntade betalningar. |
| **Rundningsfel i sista perioden** | Efter sista iterationen sätts `remaining_principal` till 0 om den blir < 0, men `payment` för sista månaden är fortfarande beräknad med tidigare ränta – totalbeloppet kan avvika något från `total_payment`. |
| **Datumberäkning (`end_date`)** | Använder `today.replace(...)`. Vid t.ex. 31‑jan + 1 månad blir datumet 28/29‑feb (behåller dag). Detta bör testas för månader med färre dagar. |
| **Return‑nycklar** | GUI förväntar sig `remaining_principal` i schemat – finns. `type` är `"loan"` vilket matchar GUI‑kontrollen (`result[\"type\"] == \"loan\`). |

**Testförslag**
1. Normalt lån: 100 000 SEK, 5 % årsränta, 60 månader → jämför med extern kalkylator.
2. Nollränta: `rate = 0` → lika stora betalningar utan ränta.
3. Nollmånad: `term_months = 0` (både med och utan ränta) → förväntat undantag eller tydligt felmeddelande.
4. Negativ ränta: verifiera att funktionen antingen kastar ett meningsfullt fel eller returnerar rimliga värden.

### 2.3 `calculate_lease`
| Potentiell bug / edge case | Kommentar |
|----------------------------|-----------|
| **Division med noll** (`term_months == 0`) | Handledas – ger `monthly_depreciation = 0` men ränta beräknas ändå. Resultatet blir enbart räntekostnad, vilket är ologiskt för ett avtal utan löptid. |
| **Negativ residual** (`residual_value < 0`) | Ingen kontroll – kan göra `total_depreciation` > lease_amount och ge negativ avskrivning. |
| **Residual ≥ lease_amount** | Ger noll eller negativ avskrivning → negativa månadskostnader. GUI har en kontroll, men om funktionen anropas direkt bör den också validera. |
| **Negativ ränta** – samma problem som för lån. |
| **Datumberäkning** – identisk med lånet. |

**Testförslag**
1. Standardleasing: 200 000 SEK, 4 % årsränta, 36 månader, residual 50 000 SEK.
2. Nollmånad → förvänta ett fel eller tydlig varning.
3. Residual ≥ amount – anropa funktionen direkt och bekräfta att den returnerar rimliga (eller negativa) värden; bör kompletteras med validering i GUI.

---

## 3️⃣ GUI‑modulen (`gui.py`)
### 3.1 Allmänna UI‑aspekter
| Punkt | Möjlig problematik |
|-------|--------------------|
| Import av `QtGui.QFont` men aldrig använd | Små ineffektivitet, ingen funktionell påverkan. |
| `self.save_button.setEnabled(True)` / `export_button` – bara efter lyckad beräkning. Kontrollera att de är inaktiverade från början. |
| Signal‑dubbelkoppling | Om `init_ui` anropas flera gånger kan knappar få dubbla anslutningar → dubbel körning av callbacks. |
| Svenskt talformat – `_fmt_belopp` byter “,” till ” ” och “.” till ”,”, men `locale` används inte. Kan ge inkonsekvent formatering i vissa miljöer. |

### 3.2 Inmatningsparsning (`_parse_decimal`)
| Problem | Kommentar |
|--------|-----------|
| Ingen felhantering – vid t.ex. "abc" kastas `ValueError`. Fångas av en generell `except Exception` i `on_calculate`, vilket ger ett ospecificerat felmeddelande. |
| Tomma strängar → `float("")` → `ValueError`. Det hanteras av tidigare tom‑kontroll men kan förbättras. |

### 3.3 Beräkning (`on_calculate`)
| Potentiella fel | Kommentar |
|-----------------|-----------|
| Felmeddelande för residual – valideras bara när `loan_type == "Leasing"`. Om användaren byter typ efter att ha skrivit in ett residual‑värde och döljer fältet, påverkas inte beräkningen (korrekt). |
| Ingen hantering av extremt stora tal – UI kan bli otydlig men programmet kraschar ej. |
| Flera anrop i snabb följd – knappen “Beräkna” är inte inaktiverad under körning, så dubbla klick kan leda till race‑condition på `self.current_result`. |

### 3.4 Tabelluppdateringar
- `update_summary_table` rensar med `clear()` och sätter rubriker igen – onödigt dyrt men ok för bara 6 rader.
- `summary_table.setEditTriggers(QTableWidget.NoEditTriggers)` kan flyttas till init‑delen. 

### 3.5 Diagramuppdatering (`update_chart`)
| Problem | Kommentar |
|--------|-----------|
| `self.ax.clear()` återställer även titel/etiketter – de sätts sedan på nytt (ok). |
| Färger hårdkodade – kan vara svåra för färgblindhet. |
| Ingen hantering av tomt schema (`term_months = 0`). Diagram blir tomt utan felmeddelande. |

### 3.6 Databasinteraktion (`database.py`)
- GUI antar att `Database` implementerar `save_calculation`, `get_all_calculations` och `delete_calculation`. Kontrollera att:
  * Sökvägen till databasen är skrivbar.
  * Metoderna kastar tydliga undantag vid fel (fil‑lås, korrupt DB). |

### 3.7 PDF‑export (`report.py`)
- `generate_pdf_report(filepath, result)` bör hantera:
  * Fil‑skrivrättigheter.
  * Överskrivning av befintlig fil – GUI frågar inte användaren, så en befintlig fil skrivs över utan varning.
  * Fel vid PDF‑generering (saknade teckensnitt) – fångas av GUI och visas som generellt fel. |

### 3.8 Konfigurationsfil (`config.json`)
- Läsning sker i `__init__`. Vid korrupt JSON faller tillbaka på defaults – bra.
- `use_swedish_format` styr både talformat och decimal‑separator i UI.

---

## 4️⃣ Testplan (manuell + automatiserad)
| Steg | Vad som testas | Förväntat resultat |
|------|----------------|--------------------|
| **1. Starta appen** | Ingen exception, huvudfönster visas | Fönstret öppnas med tomma fält |
| **2. Grundläggande lån** | 100 000 SEK, 5 %, 60 m | Månadskostnad ≈ 1 887 kr, total ≈ 113 200 kr; diagram & schema fylls |
| **3. Nollränta** | Ränta = 0, 12 månader | Månadskostnad = belopp/term, ingen räntedel i diagrammet |
| **4. Negativ ränta** | -1 % → bör visa felmeddelande (eller åtminstone inte krascha) |
| **5. Nollmånad** | Term = 0 → förväntat undantag / tydligt fel (t.ex. “Löptid måste vara > 0”) |
| **6. Leasing med residual** | 200 000, 4 %, 36 m, residual 50 000 | Samma kontroll som lånet men med `type = lease` och rätt nycklar (`remaining_balance`) |
| **7. Residual ≥ belopp** | Försök spara via UI – ska visa fel innan kalkyl |
| **8. Växla typ** | Skriv in leasing‑värden, byt till lån → residualfältet göms och påverkar inte beräkning |
| **9. Historik** | Spara en beräkning, gå till “Historik”, ladda den, radera den – tabellen uppdateras korrekt |
| **10. Export PDF** | Exportera en beräkning → fil skapas, öppnas i PDF‑läsare och innehåller samma siffror som UI |
| **11. Stora tal / långa löptider** (t.ex. 5 000 000 SEK, 120 m) – kontrollera att tabeller/diagram inte kraschar eller blir otydliga |
| **12. Edge‑case datum** | Startdatum = 31‑jan + 1 månad → slutdatum bör bli 28‑feb (eller 29‑feb) |
| **13. Dubbelklick på “Beräkna”** – UI ska inte skapa två resultat eller dubbla poster i historiken |
| **14. Felhantering** – Stäng av skrivbehörighet för databasen / PDF‑mappen och verifiera att GUI visar ett tydligt felmeddelande utan crash |

---

## 5️⃣ Rekommenderade förbättringar (för framtida iteration)
1. **Input‑validering** – Lägg till specifika `ValueError`‑meddelanden i `_parse_decimal` så att `on_calculate` kan visa exakt vad som är fel.
2. **Hantera nollmånad / nollränta** – Kasta egna undantag med tydliga meddelanden innan beräkning påbörjas.
3. **Negativ ränta & residual** – Lägg till guard‑satser i UI (och eventuellt i kalkylatorn) för att avvisa dessa värden.
4. **Disable “Beräkna” under körning** – Undvik race‑conditions vid snabba klick.
5. **Separera datumlogik** – Använd `dateutil.relativedelta` eller egen funktion som hanterar månader med olika antal dagar mer robust.
6. **Konfigurationshantering** – Ladda config via en separat klass så att UI kan reagera på ändrade inställningar utan omstart.
7. **Enhetstester** – Skriv pytest‑tester för `calculate_loan` och `calculate_lease` med parametriserade edge‑cases (noll, negativt, stora tal).
8. **Internationellisering** – Använd `QLocale` för talformat istället för egen string‑manipulation.

---

## 6️⃣ Nästa steg
1. Kör den manuella testplanen ovan och notera eventuella fel eller oväntade beteenden.
2. Implementera de mest kritiska förbättringarna (t.ex. input‑validering, nollmånad‑hantering).
3. Lägg till automatiserade enhetstester för kalkylatorfunktionerna.
4. Vid behov, uppdatera `database.py` och `report.py` så att felmeddelanden blir mer informativa.

När du har kört testerna eller vill gå vidare med någon av förbättringarna, säg bara till så fortsätter vi!