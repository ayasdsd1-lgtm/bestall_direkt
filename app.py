from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import psycopg2
import os
import re      # Används för formatvalidering vid registrering
from flask import jsonify


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
    Sökfunktion för startsidan.

    Denna route:
    1. Hämtar sökordet från URL:en (t.ex. /search?q=brunch)
    2. Söker i databasen efter företag som matchar sökordet
    3. Skickar resultatet till search.html för visning
    """

    # Hämtar det användaren skrev i sökfältet
    # request.args används eftersom formuläret använder method="GET"
    # "q" måste matcha name="q" i HTML-inputen
    query = request.args.get("q", "").strip()

    # Skapar en cursor för att kunna prata med databasen
    cursor = conn.cursor()

    try:
        # SQL-fråga:
        # ILIKE = case-insensitive (både "brunch" och "Brunch" funkar)
        # % betyder "matcha vad som helst före/efter"
        # Vi söker både på företagsnamn och kategori
        cursor.execute(
            """
            SELECT foretagare_id, foretagsnamn, kategori, email, telefon
            FROM public.foretagare
            WHERE foretagsnamn ILIKE %s
               OR kategori ILIKE %s
            """,
            (f"%{query}%", f"%{query}%")
        )

        # Hämtar alla matchande rader från databasen
        resultat = cursor.fetchall()

    except Exception as e:
        # Om något går fel i databasen
        print("Fel vid sökning:", e)
        resultat = []

    # Tillfällig testdata om databasen inte ger några träffar
    # Detta gör att vi kan testa search.html även innan databasen är färdig
    if not resultat:
        test_foretag = [
            (1, "Sushi Express", "Sushi", "info@sushi.se", "0701234567"),
            (2, "Italiensk Buffé AB", "Buffé", "info@buffe.se", "0702222222"),
            (3, "Brunch & Co", "Brunch", "info@brunch.se", "0703333333"),
            (4, "Sushi House", "Sushi", "kontakt@sushihouse.se", "0704444444"),
            (5, "Vegansk Catering", "Veganskt", "hej@vegansk.se", "0705555555")
        ]

        for foretag in test_foretag:
            if query.lower() in foretag[1].lower() or query.lower() in foretag[2].lower():
                resultat.append(foretag)

    # Skickar resultatet + sökordet till HTML-sidan
    # search.html ansvarar för att visa listan
    return render_template("search.html", resultat=resultat, query=query)


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
    Visar företagssidan för ett specifikt företag baserat på company_id i URL:en.
    OBS: Använder testdata tills företagstabellen i databasen är kopplad.
    HTML-sida: view.html
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


@app.route('/skapa_bestallning', methods=['POST'])
def skapa_bestallning():
    """
    Tar emot kunduppgifter och orderdetaljer via POST och sparar dem i tabellen 'bestallningar'.
    Returnerar JSON med success: True vid lyckad beställning, annars success: False och statuskod 500.
    Formuläret i HTML ska ha method="POST" och action="{{ url_for('skapa_bestallning') }}".
    HTML-sida: view.html
    """
    
    kund_namn = request.form.get('kund_namn')
    hemadress = request.form.get('hemadress')
    epost = request.form.get('epost')
    telefonnummer = request.form.get('telefonnummer') 

    order_detaljer = request.form.get('order_data')
    total_pris = request.form.get('total_pris')

    cursor = conn.cursor()

    try:
        query = """
        INSERT INTO bestallningar
        (kund_namn, hemadress, epost, telefonnummer, order_detaljer, total_pris)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        cursor.execute(query, (
            kund_namn,
            hemadress,
            epost,
            telefonnummer,
            order_detaljer,
            total_pris
        ))
        conn.commit()
        return jsonify({"success": True, "message": f"Tack för din beställning, {kund_namn}!"})
    
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": f"Beställningen gick inte igenom. "}), 500


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
            stored_password = user[0]
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
    """
    namn          = request.form.get("namn", "").strip()
    personnummer  = request.form.get("personnummer", "").strip()
    email         = request.form.get("email", "").strip()
    tel           = request.form.get("tel", "").strip()
    losenord      = request.form.get("losenord", "")

    # Samla alla fältfel i en ordbok så HTML kan visa dem per fält
    fel = {}

    # Namn
    if not namn:
        fel["namn"] = "Namn är obligatoriskt."
    elif len(namn) < 2:
        fel["namn"] = "Namnet är för kort."

    # Personnummer – format YYYYMMDD-XXXX eller YYYYMMDDXXXX
    if not personnummer:
        fel["personnummer"] = "Personnummer är obligatoriskt."
    elif not re.fullmatch(r"\d{8}-?\d{4}", personnummer):
        fel["personnummer"] = "Ange personnummer i format YYYYMMDD-XXXX."

    # E-post
    if not email:
        fel["email"] = "E-postadress är obligatorisk."
    elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        fel["email"] = "Ange en giltig e-postadress."

    # Mobilnummer – 10 siffror, får börja med +46
    if not tel:
        fel["tel"] = "Mobilnummer är obligatoriskt."
    elif not re.fullmatch(r"(\+46|0)\d{9}", tel.replace(" ", "").replace("-", "")):
        fel["tel"] = "Ange ett giltigt mobilnummer (t.ex. 0701234567)."

    # Lösenord
    if not losenord:
        fel["losenord"] = "Lösenord är obligatoriskt."
    elif len(losenord) < 8:
        fel["losenord"] = "Lösenordet måste vara minst 8 tecken."

    # Om valideringsfel finns – returnera sidan med alla felmeddelanden
    if fel:
        return render_template(
            "register.html",
            fel=fel,
            # Skicka tillbaka ifyllda värden så användaren inte behöver skriva om allt
            prev={"namn": namn, "personnummer": personnummer, "email": email, "tel": tel}
        )

    cursor = conn.cursor()

    try:
        # Kolla om emailen redan är registrerad
        cursor.execute(
            "SELECT id FROM public.foretagare WHERE email = %s",
            (email,)
        )
        if cursor.fetchone():
            fel["email"] = "Den här e-postadressen är redan registrerad."
            return render_template(
                "register.html",
                fel=fel,
                prev={"namn": namn, "personnummer": personnummer, "email": email, "tel": tel}
            )

        # Hasha lösenordet innan det sparas i databasen
        hashat_losenord = generate_password_hash(losenord)

        cursor.execute(
            """INSERT INTO public.foretagare
               (foretagsnamn, personnummer, email, telefon, losenord)
               VALUES (%s, %s, %s, %s, %s)""",
            (namn, personnummer, email, tel, hashat_losenord)
        )
        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Fel vid registrering: {e}")
        return render_template(
            "register.html",
            fel={"general": "Något gick fel, försök igen."},
            prev={"namn": namn, "personnummer": personnummer, "email": email, "tel": tel}
        )

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
# Profile sidan
# -------------------------------------------------------
@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect(url_for("logga_in"))
    
    email = session["user"]
    cursor = conn.cursor()

    try:
        query = """
            SELECT
                b.bestallning_id,
                b.datum,
                k.namn AS kund_namn,
                k.telefonnummer,
                m.menynamn,
                br.antal
            FROM public.foretagare f
            JOIN public.verksamhet v ON f.foretagare_id = v.foretagare_id
            JOIN public.bestallningar b ON v.verksamhet_id = b.verksamhet_id
            JOIN public.kund k ON b.kund_id = k.kund_id
            JOIN public.bestallningsrad br ON b.bestallning_id = br.bestallning_id
            JOIN public.meny m ON br.meny_id = m.meny_id
            WHERE f.email = %s
            ORDER BY b.datum DESC
        """

        cursor.execute(query, (email, ))
        bokningar = cursor.fetchall()

        return render_template("profile.html", bokningar=bokningar)
    
    except Exception as e:
        print(f"Gick inte att ladda upp profilsidan: {e}")
        return "Ett fel uppstod", 500



# -------------------------------------------------------
# STARTA SERVERN
# -------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)

