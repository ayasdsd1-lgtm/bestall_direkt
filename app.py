from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import psycopg2
import os


load_dotenv() # laddar in .env-filen som innehåller databas-info

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")  # Hämtar hemlig nyckel från .env

# Databasanslutning via miljövariabel - Supabase kräver SSL
conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")

# -------------------------------------------------------
# STARTSIDAN
# -------------------------------------------------------

@app.route("/")
def home():
    """
    Startsidan. Renderar index.html
    HTML-sida: index.html
    """
    return render_template("index.html")

# -------------------------------------------------------
# SÖK
# -------------------------------------------------------

@app.route("/search")
def search():
    """ 
    Hämtar det användaren skrev i sökrutan (name="q").
    Formuläret i HTML ska ha method="GET" och action="/search".
    OBS: input i HTML måste ha name="q" för att detta ska fungera.

    HTML-sida: search.html (ej byggd än)
    """

    """
    # När search.html är byggd, använd det här:
    query = request.args.get('q')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM public.foretagare WHERE foretagsnamn ILIKE %s",
        (f"%{query}%",)
    )
    resultat = cursor.fetchall()
    return render_template("search.html", resultat=resultat, query=query)
    """
    return f"<h1>Sökresultat</h1><p>Du söker efter: {query}</p><a href='/'>Tillbaka till start</a>"


# -------------------------------------------------------
# KATEGORIER
# -------------------------------------------------------

@app.route("/kategori/<namn>")
def kategori(namn):
    """
    Visar en sida för en specifik catering-kategori.
    Länken i HTML ska se ut: {{ url_for('kategori', namn='Brunch') }}
    HTML-sida: kategori.html
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM public.foretagare WHERE kategori = %s",
        (namn,)
    )
    foretag = cursor.fetchall()
    return render_template("kategori.html", namn=namn, foretag=foretag)


@app.route("/alla-kategorier")
def alla_kategorier():
    """
    Visar en sida med alla catering-kategorier.
    Länken i HTML ska se ut: {{ url_for('alla_kategorier') }}
    HTML-sida: alla_kategorier.html (ej byggd än)
    """
    return "<h1>Här listas alla våra catering-kategorier</h1>"


# -------------------------------------------------------
# VIEW
# -------------------------------------------------------
@app.route("/view/<int:company_id>") # /<id> måste läggas till när en tabell i databasen har kopplats
def view_company(company_id):
    """
    Visar en sidan på företagssidor som visas för kunder när
    de trycker på en specifik sida.
    """
    test_data = {
        "namn": "Ajabaja AB",
        "adress": "ingenstans 123",
        "telefon": "0712345678",
        "epost": "ajabaja@ajabaja.com",
        "beskrivning": "Gottegott gottegott",
        "tjanster":[
            {"namn": "Dolma", "beskrivning": "Vinblad fyllda med ris, köttfärs och kryddor" ,"pris": 10},
            {"namn": "Mini cheesecake", "beskrivning": "Bakverk innehållande färskost" ,"pris": 20}
        ]
    }
    return render_template("view.html", foretag=test_data)



# -------------------------------------------------------
# INLOGGNING
# -------------------------------------------------------

@app.route("/logga-in")
def logga_in():

    """
    Visar inloggningssidan för företagare
    Länken i HTML ska se ut: {{ url_for('logga_in') }}
    HTML-sida: log_in.html
    """
    return render_template("log_in.html")


@app.route("/login", methods=["POST"])
def login():
    """
    Hanterar inloggning för företagare.
    Tar emot email och lösenord via POST och jämför
    lösenordet mot det hashade värdet i databasen.
    Vid lyckad inloggning sparas email i sessionen
    och användaren skickas till startsidan.
    Formuläret i HTML ska ha method="POST" och action="/login".
    HTML-sida: log_in.html
    """
    email = request.form["email"]
    password = request.form["password"]

    cursor = conn.cursor()

    try:
        # Hämta bara via email
        cursor.execute(
            "SELECT * FROM public.foretagare WHERE email = %s",
            (email,)
        )
        user = cursor.fetchone()

        if user:
            stored_password = user[3]
            if check_password_hash(stored_password, password):
                # session: Sparar inloggad användare i sessionen
                session["user"] = email 
                return redirect(url_for("home"))
            else:
                # ÄNDRAT: returnerar sidan med felmeddelande istället för ren text
                return render_template("log_in.html", fel="Fel lösenord")
        else:
            # ÄNDRAT: returnerar sidan med felmeddelande istället för ren text
            return render_template("log_in.html", fel="Användaren finns inte")

    except Exception as e:
        conn.rollback()
        print("FEL:", e)
        # ÄNDRAT: returnerar sidan med felmeddelande istället för ren text
        return render_template("log_in.html", fel="Något gick fel, försök igen")
    

# -------------------------------------------------------
# REGISTRERING
# -------------------------------------------------------

@app.route("/registrering")
def registrera_sig():

    """
    Visar registreringssidan för företagare.
    Länken i HTML ska se ut: {{ url_for('registrera_sig') }}
    HTML-sida: register.html
    """
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register():
    """
    Registrerar en ny företagare i databasen.
    Tar emot namn, email och lösenord via POST.
    Kollar först om emailen redan finns i databasen.
    Lösenordet hashas innan det sparas.
    Efter lyckad registrering skickas användaren till inloggningssidan.
    Formuläret i HTML ska ha method="POST" och action="/register".
    HTML-sida: register.html

    OBS: personnummer och mobilnummer läggs till när databasen är redo.
    """
    namn = request.form["namn"]
    email = request.form["email"]
    losenord = request.form["losenord"]

    # personnummer = request.form["identification"]  ← lägg till när databasen är redo
    # tel = request.form["tel"]                      ← lägg till när databasen är redo

    cursor = conn.cursor()

    try:
        # Kolla om emailen redan är registrerad
        cursor.execute(
            "SELECT * FROM public.foretagare WHERE email = %s",
            (email,)
        )
        if cursor.fetchone():
            # ÄNDRAT: returnerar sidan med felmeddelande istället för ren text
            return render_template("register.html", fel="Email redan registrerad")

        # Hasha lösenordet innan det sparas i databasen
        hashat_losenord = generate_password_hash(losenord)

        cursor.execute(
            "INSERT INTO public.foretagare (foretagsnamn, email, losenord) VALUES (%s, %s, %s)",
            (namn, email, hashat_losenord)
        )
        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Fel vid registrering: {e}")
        # ÄNDRAT: returnerar sidan med felmeddelande istället för ren text
        return render_template("register.html", fel="Något gick fel, försök igen")

    # Skicka användaren till inloggningssidan efter lyckad registrering
    return redirect(url_for("logga_in"))



# -------------------------------------------------------
# UTLOGGNING
# -------------------------------------------------------

@app.route("/logga-ut")
def logga_ut():
    """
    Loggar ut den inloggade användaren genom att rensa sessionen.
    Skickar användaren tillbaka till startsidan.
    Länken i HTML ska se ut: {{ url_for('logga_ut') }}
    """
    session.clear()      # Raderar minneslappen - användaren är ut utloggad
    return redirect(url_for("home"))


# -------------------------------------------------------
# Info sidan
# -------------------------------------------------------
@app.route("/info")
def info():
    """
    Visar info sidan för besökare
    Länken i HTML ska se ut: {{ url_for('info') }}
    HTML-sidan: info.html
    """
    return render_template("info.html")



# -------------------------------------------------------
# STARTA SERVERN
# -------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)

