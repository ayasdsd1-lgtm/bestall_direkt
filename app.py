from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import psycopg2
import os

load_dotenv() # laddar in .env-filen som innehåller databas-info

app = Flask(__name__)
app.secret_key = "hemlig_nyckel"

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
    Hämtar det användaren skrev i rutan med name="q"
    """
    query = request.args.get('q')
    return f"<h1>Sökresultat</h1><p>Du söker efter: {query}</p><a href='/'>Tillbaka till start</a>"


# -------------------------------------------------------
# KATEGORIER
# -------------------------------------------------------

@app.route("/kategori/<namn>")
def kategori(namn):
    """
    Visar en sida för en specifik catering-kategori.
    Länken i HTML ska se ut: {{ url_for('kategori', namn='Brunch') }}
    HTML-sida: kategori.html (ej byggd än)
    """
    return f"<h1>Välkommen till {namn}</h1><p>Här kommer vi visa alla tjänster inom {namn}.</p>"


@app.route("/alla-kategorier")
def alla_kategorier():
    """
    Visar en sida med alla catering-kategorier.
    Länken i HTML ska se ut: {{ url_for('alla_kategorier') }}
    HTML-sida: alla_kategorier.html (ej byggd än)
    """
    return "<h1>Här listas alla våra catering-kategorier</h1>"


# -------------------------------------------------------
# INLOGGNING OCH REGISTRERING
# -------------------------------------------------------

@app.route("/logga-in")
def logga_in():

    """
    Visar inloggningssidan för företagare
    Länken i HTML ska se ut: {{ url_for('logga_in') }}
    HTML-sida: loggaIn.html
    """
    return render_template("loggaIn.html")


@app.route("/login", methods=["POST"])
def login():
    """
    Hanterar inloggning för företagare.
    Tar emot email och lösenord via POST och jämför
    lösenordet mot det hashade värdet i databasen.
    Vid lyckad inloggning sparas email i sessionen
    och användaren skickas till startsidan.
    Formuläret i HTML ska ha method="POST" och action="/login".
    HTML-sida: loggaIn.html
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
            stored_password = user[3]  # rätt index 
            if check_password_hash(stored_password, password):
                session["user"] = email # Sparar inloggad användare i sessionen
                return redirect(url_for("home"))
            else:
                return "Fel lösenord"
        else:
            return "Användare finns inte"

    except Exception as e:
        conn.rollback()
        print("FEL:", e)
        return "Login error"
    

@app.route("/register", methods=["POST"])
def register():
    """
    Registrerar en ny företagare i databasen.
    Tar emot företagsnamn, email och lösenord via POST.
    Kollar först om emailen redan finns i databasen.
    Lösenordet hashas innan det sparas.
    Efter lyckad registrering skickas användaren till inloggningssidan.
    Formuläret i HTML ska ha method="POST" och action="/register".
    HTML-sida: loggaIn.html
    """
    namn = request.form["namn"]
    email = request.form["email"]
    losenord = request.form["losenord"]

    hashat_losenord = generate_password_hash(losenord)

    cursor = conn.cursor()

    try:
        # Kolla om emailen redan är registrerad
        cursor.execute(
            "SELECT * FROM public.foretagare WHERE email = %s",
            (email,)
        )
        if cursor.fetchone():
            return "Email redan registrerad"

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
        return "Fel vid registrering"

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







if __name__ == "__main__":
    app.run(debug=True)
