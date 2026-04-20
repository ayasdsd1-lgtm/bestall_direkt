import psycopg2

conn = psycopg2.connect(
    dbname="Bestall_Direkt",
    user="postgres",
    password="1234",
    host="localhost",
    port="5432"
)

cursor = conn.cursor()


from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def home():
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
    En specifik sida för HTML classen 'card-all'
    """
    return "<h1>Här listas alla våra catering-kategorier</h1>"

@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    password = request.form["password"]

    cursor.execute(
        "SELECT * FROM foretagare WHERE email = %s AND losenord = %s",
        (email, password)
    )

    user = cursor.fetchone()

    if user:
        return "Inloggad"
    else:
        return "Fel uppgifter"


if __name__ == "__main__":
    app.run(debug=True)