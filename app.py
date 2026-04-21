from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import psycopg2
import os

load_dotenv() #laddar in .env-filen som innehåller databas-info

app = Flask(__name__)
app.secret_key = "hemlig_nyckel"

conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require") #Databasanslutning via miljövariabel
cursor = conn.cursor()


@app.route("/")
def home():
    """
    Startsidan. Renderar index.html
    """
    return render_template("index.html")

@app.route("/logga-in")
def logga_in():

    """
    Visar inloggningssidan för företagare
    """
    return render_template("loggaln.html")

@app.route("/search")
def search():
    """ 
    Hämtar det användaren skrev i rutan med name="q"
    """
    query = request.args.get('q')
    return f"<h1>Sökresultat</h1><p>Du söker efter: {query}</p><a href='/'>Tillbaka till start</a>"


@app.route("/kategori/<namn>")
def kategori(namn):
    """
    Här kan man senare lägga till logik för att visa olika maträtter
    """
    return f"<h1>Välkommen till {namn}</h1><p>Här kommer vi visa alla tjänster inom {namn}.</p>"



@app.route("/alla-kategorier")
def alla_kategorier():
    """
    Visar en sida med alla catering-kategorier.
    Används av HTML-classen 'card-all' på startsidan.
    """
    return "<h1>Här listas alla våra catering-kategorier</h1>"



@app.route("/login", methods=["POST"])
def login():
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
                return "Inloggad"
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
    Lösenordet hashas innan det sparas.
    """
    namn = request.form["namn"]
    email = request.form["email"]
    losenord = request.form["losenord"]

    hashat_losenord = generate_password_hash(losenord)

    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO public.foretagare (foretagsnamn, email, losenord) VALUES (%s, %s, %s)",
            (namn, email, hashat_losenord)
        )
        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Fel vid registrering:{e}")
        return "Fel vid registrering"

    return "Användare skapad!"


if __name__ == "__main__":
    app.run(debug=True)
