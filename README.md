# BoNT-A Spasticity Research Dashboard

## Fajlovi
- `app.py` — glavna Streamlit aplikacija (UI, filteri, grafici)
- `dashboard_logic.py` — sva logika za mapiranje kolona i wide→long transformaciju (testirano nezavisno)
- `requirements.txt` — potrebni paketi

## Pokretanje lokalno
```bash
pip install -r requirements.txt
streamlit run app.py
```
Aplikacija po defaultu traži `baza.xlsx` u istom folderu. Ako ga nema, pojaviće se
uploader u sidebar-u gde možeš ručno da učitaš Excel fajl.

## Prelazak na Google Sheets
U `app.py`, funkcija `load_google_sheet()` je pripremljena kao "shell" — treba:
1. `pip install gspread google-auth`
2. Napraviti Google service account i sačuvati JSON u `.streamlit/secrets.toml` pod ključem `gcp_service_account`
3. Deliti Google Sheet sa email-om service account-a (viewer pristup je dovoljan)
4. Otkomentarisati kod unutar `load_google_sheet()` i staviti URL sheet-a u sidebar polje

Struktura podataka (kolone) ostaje identična — logika u `dashboard_logic.py`
radi nezavisno od izvora podataka, samo prima `pandas.DataFrame`.

## Šta je provereno
- Sva imena kolona (uključujući nepravilnosti razmaka kod "30PF"/"30 PF" za
  9. i pojedine 12. mesece) generisana su i **tačno upoređena** sa realnom
  listom od 142 merene kolone — 100% poklapanje.
- `to_long()`, `recode_spasticity()` (1+ → 1.5) i `summarize()` testirani su
  jediničnim testovima na sintetičkim podacima (22 pacijenta).
- Aplikacija je pokrenuta pravim `streamlit run` serverom i učitava se bez grešaka.

## Napomena o uzorku
Ukupan uzorak je ~22 pacijenta. Ispod svakog panela prikazan je broj pacijenata
(n) koji su doprineli podacima za tu specifičnu varijablu/podfilter, jer se
taj broj može razlikovati od ukupnog uzorka usled filtera i nedostajućih vrednosti.

## Univerzalni filteri (sidebar)
- **Side of stroke** — multiselect
- **Earlier BoNT-A treatment in legs** — multiselect (Yes/No mogu zajedno)
- **Age at stroke** — dvostrani slajder
- **Days between stroke and BoNT-A** — dvostrani slajder, otključava se samo
  ako je "Yes" izabrano za prethodni filter; pacijenti sa "No" (bez vrednosti)
  se uvek zadržavaju bez obzira na ovaj slajder.

## Kategorije merenja (glavna stranica)
Svaka kategorija ima svoje dodatne pod-filtere gde je primenljivo (mišić,
pozicija merenja, itd.), i tri tipa prikaza: Error Bars, Line Plot
(spaghetti — hover prikazuje ID pacijenta i podatke iz univerzalnih filtera),
i Boxplot. Affected/Non Affected (ili Left/Right, ili PF/DF, ili AROM/PROM)
se prikazuju u dve kolone jedna pored druge.
