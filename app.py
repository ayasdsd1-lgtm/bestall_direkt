from flask import Flask, render_template, request
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import psycopg2
import os

load_dotenv() #laddar in .env-filen som innehåller databas-info

app = Flask(__name__)
app.secret_key = "hemlig_nyckel"

conn = psycopg2.connect(os.getenv("DATABASE_URL")) #Databasanslutning via miljövariabel
cursor = conn.cursor()


@app.route("/")
def home():
    """
    Startsidan. Renderar index.html
    """
    return render_template("index.html")


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
    """
    Hanterar inloggning för företagare.
    Tar emot email och lösenord via POST, söker efter användaren i
    databasen och jämför lösenordet mot det hashade värdet.
    """
    email = request.form["email"]
    password = request.form["password"]

    cursor.execute(
        "SELECT * FROM foretagare WHERE email = %s AND losenord = %s",
        (email, password)
    )
    user = cursor.fetchone()

    if user and check_password_hash(user[2], password):
        return "Inloggad"
    else:
        return "Fel uppgifter"
    


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

    cursor.execute(
        "INSERT INTO foretagare (foretagsnamn, email, losenord) VALUES (%s, %s, %s)",
        (namn, email, hashat_losenord)
    )
    conn.commit()

    return "Användare skapad!"


if __name__ == "__main__":
    app.run(debug=True)
