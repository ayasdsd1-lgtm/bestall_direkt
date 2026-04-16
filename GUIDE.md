# Guide för HTML-utveckling i Beställ Direkt

📝 Viktigt för HTML-utveckling
Vi använder nu Flask för att driva sidan. För att allt ska fungera ihop med app.py, tänk på följande:


## 1. Länkar (Navigering)
Använd Flasks `url_for` istället för vanliga filnamn. 
T.ex. href="{{ url_for('kategori', namn='Brunch') }}" istället för tomma länkar.

- **Startsidans länk:** `{{ url_for('home') }}`
- **Söksidan:** `{{ url_for('search') }}`
- **Kategorier:** `{{ url_for('kategori', namn='Brunch') }}`


## 2. Bilder
Alla bilder måste laddas via mappen `static/images`.

Exempel:
`<img src="{{ url_for('static', filename='images/bildnamn.jpg') }}" alt="Beskrivning">`


## 3. Sökfältet
För att sökfunktionen i `app.py` ska fungera måste formuläret se ut så här:

- Form action: `/search`
- Form method: `GET`
- Input name: `q`
