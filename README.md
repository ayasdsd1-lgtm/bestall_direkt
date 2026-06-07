# bestall_direkt

## Länk till kod, version 1.4  
https://github.com/ayasdsd1-lgtm/bestall_direkt/releases/tag/v.1.4

---

## Hur man öppnar projektet lokalt

1. Öppna mappen `bestall_direkt` i Visual Studio Code
2. Installera Python: Se till att du har `Python` installerat på din dator.
3. Installera beroenden: Se till att du har `Flask` installerat på din dator.
4. Skapa .env-filen: Kopiera `.env.example` och döp om den till `.env`
5. Kör projektet: Öppna filen `app.py`. Klicka på play-knappen (▶) uppe i högra hörnet i VS Code. När du ser en länk i terminalen, håll in `Ctrl` och klicka på den för att öppna projektet i webbläsaren: `http://127.0.0.1:5000`

---

## Databas

Projektet använder **Supabase** (PostgreSQL) som databas.

### Alternativ A – Kör mot vår Supabase-instans (rekommenderas)

Fyll i följande värden i din `.env`-fil (se `.env.example`):

```
SUPABASE_URL=<projektets URL>
SUPABASE_KEY=<projektets anon-nyckel>
```

Kontakta gruppen om du behöver inloggningsuppgifter.

### Databasfiler

| Fil | Innehåll |
|-----|----------|
| `database/schema.sql` | Tabeller, kolumner och relationer |

---

## Projektstruktur

```
bestall_direkt/
├── app.py              ← Starta projektet härifrån
├── .env.example        ← Mall för miljövariabler
├── .env                ← Skapas lokalt (ingår ej i zip)
├── database/
│   └── schema.sql      ← Databaskod (Supabase/PostgreSQL)
├── static/             ← CSS, bilder, JS
└── templates/          ← HTML-mallar
```
