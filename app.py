from sqlite3 import Cursor
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import psycopg2
import os
import re      # Används för formatvalidering vid registrering
from flask import jsonify
import json


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

    query = request.args.get("q", "").strip()

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
           SELECT DISTINCT v.verksamhet_id, v.verksamhetsnamn, v.kategori
            FROM public.verksamhet v
            LEFT JOIN public.meny m ON m.verksamhet_id = v.verksamhet_id
            WHERE v.verksamhetsnamn ILIKE %s
                OR v.kategori        ILIKE %s
                OR v.beskrivning     ILIKE %s
                OR m.menynamn        ILIKE %s
                OR m.beskrivning     ILIKE %s
            """,
            (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%")
        )

        resultat = cursor.fetchall()

    except Exception as e:
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
    Visar alla företag som tillhör en viss kategori.
    """
    kategorier = {
    "Smatt-och-mingel": "Smått & mingel",
    "Middag-och-festmat": "Middag & festmat",
    "Bakver-och-sott": "Bakverk & sött",
    "Buffe": "Buffé",
    "Brunch": "Brunch"
}

    visningsnamn = kategorier.get(namn, namn.replace("-", " "))

    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT * FROM public.verksamhet WHERE kategori = %s",
            (visningsnamn,)
        )

        foretag = cursor.fetchall()

    except Exception as e:
        conn.rollback()
        print("Fel vid kategori:", e)
        foretag = []
    
    # Hårdkodad testdata för kategorin Sushi
    if not foretag and visningsnamn == "Sushi":
        foretag = [
            (1, "Sushi Express"),
            (4, "Sushi House")
        ]

    return render_template("kategori.html", namn=visningsnamn, foretag=foretag)


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

@app.route("/view/<int:company_id>") 
def view_company(company_id):
    """
    Visar företagssidan för ett specifikt företag baserat på company_id i URL:en.
    OBS: Använder testdata tills företagstabellen i databasen är kopplad.
    HTML-sida: view.html
    """

    cursor = conn.cursor()

    try:

        # Hämta verksamhetsinformation
        cursor.execute("""
            SELECT
                verksamhetsnamn,
                adress,
                telefonnummer,
                beskrivning,
                kategori,
                logo_url
            FROM public.verksamhet
            WHERE verksamhet_id = %s
        """, (company_id,))
        
        verksamhet = cursor.fetchone()

        print("Verksamhet:", verksamhet)  

        # Om verksamheten inte finns
        if not verksamhet:
            return "Verksamheten hittades inte", 404

        # Gör om databassvaret till dictionary
        foretag = {
            "namn": verksamhet[0],
            "adress": verksamhet[1],
            "telefon": verksamhet[2],
            "epost": "kontakt@bestalldirekt.se",  # tillfällig
            "beskrivning": verksamhet[3],
            "kategori": verksamhet[4],
            "logo_url": verksamhet[5],
            "tjanster": []
        }

        # Hämta tjänster/meny
        cursor.execute("""
            SELECT
                menynamn,
                beskrivning,
                pris
            FROM public.meny
            WHERE verksamhet_id = %s
        """, (company_id,))

        meny = cursor.fetchall()

        # Lägg till tjänster i listan
        for item in meny:

            foretag["tjanster"].append({
                "namn": item[0],
                "beskrivning": item[1],
                "pris": item[2]
            })

        return render_template(
            "view.html",
            foretag=foretag
        )

    except Exception as e:

        conn.rollback()

        print("Fel vid hämtning av verksamhet:", e)

        return "Ett fel uppstod", 500


@app.route('/skapa_bestallning', methods=['POST'])
def skapa_bestallning():
    """
    Tar emot kunduppgifter och orderdetaljer via POST och sparar dem i tabellen 'bestallningar'.
    Returnerar JSON med success: True vid lyckad beställning, annars success: False och statuskod 500.
    Formuläret i HTML ska ha method="POST" och action="{{ url_for('skapa_bestallning') }}".
    HTML-sida: view.html
    """
    
    namn = request.form.get('kund_namn')
    email = request.form.get('epost')
    telefon = request.form.get('telefonnummer')

    order_data = request.form.get('order_data') # JSON-sträng med produkter
    order_items = json.loads(order_data) 

    for item in order_items:
        cursor.execute("""
            INSERT INTO bestallningsrad (bestallning_id, meny_id, antal)
                       VALUES (%s, %s, %s)
                        """, (bestallning_id, item['meny_id'], item['antal']))

    cursor = conn.cursor()

    try:
        # 1. Skapa kund 
        cursor.execute("""
            INSERT INTO kund (namn, email, telefonnummer)
            VALUES (%s, %s, %s) 
            RETURNING kund_id
        """, (namn, email, telefon))

        kund_id = cursor.fetchone()[0]  # Hämta det genererade kund_id

        # 2. Skapa beställning kopplad till kunden
        cursor.execute("""
            INSERT INTO bestallningar (kund_id, verksamhet_id, status)
            VALUES (%s, %s, %s)
            RETURNING bestallning_id
            """, (kund_id, 1, 'pending'))  # Verksamhet_id = 1 som exempel
        
        bestallning_id = cursor.fetchone()[0]  # Hämta det genererade bestallning_id

        # 3. Lägg till beställningsrader
        cursor.execute("""
            INSERT INTO bestallningsrader (bestallning_id, meny_id, antal)
            VALUES (%s, %s, %s)
        """, (bestallning_id, 1, 2))  # Exempel

        conn.commit()

        return jsonify({"success": True, "message": f"Tack för din beställning, {namn}!"})
    
    except Exception as e:
        conn.rollback()
        print(e)
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

    email = request.form["email"]
    password = request.form["password"]

    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT 
                v.verksamhet_id,
                f.losenord
             FROM public.foretagare f
             LEFT JOIN public.verksamhet v
                ON f.foretagare_id = v.foretagare_id
            WHERE f.email = %s
        """, (email,))

        user = cursor.fetchone()

        print(user)

        if user:

            verksamhet_id = user[0]
            stored_password = user[1]

            if check_password_hash(stored_password, password):

                # Sparar användaren i session
                session["user"] = email

                # Skicka företagaren till dashboard/profile
                return redirect(url_for("profile"))
            
            else:
                return render_template(
                    "log_in.html",
                    fel="Fel lösenord"
                )
        else:
            return render_template(
                "log_in.html",
                fel="Användare finns inte"
            )
        
    except Exception as e:
        conn.rollback()
        print("FEL:", e)
        return render_template(
            "log_in.html",
            fel="Något gick fel, försök igen"
        )
    

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
            "SELECT foretagare_id FROM public.foretagare WHERE email = %s",
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
    return render_template("register.html", success="Ditt konto har skapats! Du kan nu logga in.")

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

@app.route("/radera-konto")
def radera_konto():

    if "user" not in session:
        return redirect(url_for("logga_in"))

    session.clear()

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
@app.route("/verksamhet")
def profile():
    """
    Visar profilsidan för inloggad företagare.
    Kontrollerar att användaren är inloggad via sessionen.
    Hämtar företagarens inkomna beställningar från databasen och skickar dem till profile.html.
    Länken i HTML ska se ut: {{ url_for('profile') }}
    HTML-sida: profile.html
    """
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

        # Hämta verksamhetsinformation
        cursor.execute("SELECT verksamhetsnamn, beskrivning, telefonnummer FROM public.verksamhet WHERE foretagare_id = (SELECT foretagare_id FROM public.foretagare WHERE email = %s)", (email,))
        verksamhet = cursor.fetchone()

        return render_template("profile.html", bokningar=bokningar, verksamhet=verksamhet)
    
    except Exception as e:
        print(f"Gick inte att ladda upp profilsidan: {e}")
        return "Ett fel uppstod", 500
    
@app.route("/uppdatera-verksamhet", methods=["POST"])
def uppdatera_verksamhet():

    if "user" not in session:
        return redirect(url_for("logga_in"))

    email = session["user"]

    verksamhetsnamn = request.form.get("verksamhetsnamn")
    beskrivning = request.form.get("beskrivning")
    telefonnummer = request.form.get("telefonnummer")
    logo_url = request.form.get("logo_url")
    kategori = request.form.get("kategori")

    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE public.verksamhet
            SET verksamhetsnamn = %s,
                beskrivning = %s,
                telefonnummer = %s,
                logo_url = %s,
                kategori = %s
            WHERE foretagare_id = (
                SELECT foretagare_id
                FROM public.foretagare
                WHERE email = %s
            )
        """, (
            verksamhetsnamn,
            beskrivning,
            telefonnummer,
            logo_url,
            kategori,
            email
        ))

        conn.commit()

        return redirect(url_for("profile"))

    except Exception as e:
        conn.rollback()
        print("Fel vid uppdatering:", e)

        return "Kunde inte uppdatera verksamheten", 500
    
@app.route("/skapa-verksamhet", methods=["GET", "POST"])
def skapa_verksamhet():

    """
    Visar sidan där företagaren kan skapa en verksamhet.
    """

    # Kontrollera att användaren är inloggad
    if "user" not in session:
        return redirect(url_for("logga_in"))

    if request.method == "POST":

        verksamhetsnamn = request.form.get("verksamhetsnamn")
        adress = request.form.get("adress")
        telefonnummer = request.form.get("telefonnummer")
        beskrivning = request.form.get("beskrivning")
        kategori = request.form.get("kategori")
        logo_url = request.form.get("logo_url")

        email = session["user"]

        cursor = conn.cursor()

        try:

            # Hämta foretagare_id från inloggad användare
            cursor.execute("""
                SELECT foretagare_id
                FROM public.foretagare
                WHERE email = %s
            """, (email,))

            foretagare_id = cursor.fetchone()[0]

            # Skapa verksamheten
            cursor.execute("""
                INSERT INTO public.verksamhet
                (
                    foretagare_id,
                    verksamhetsnamn,
                    adress,
                    telefonnummer,
                    beskrivning,
                    kategori,
                    logo_url
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING verksamhet_id
            """, (
                foretagare_id,
                verksamhetsnamn,
                adress,
                telefonnummer,
                beskrivning,
                kategori,
                logo_url
            ))

            verksamhet_id = cursor.fetchone()[0]

            conn.commit()

            return redirect(
                url_for(
                    "view_company",
                    company_id=verksamhet_id
                )
            )

        except Exception as e:

            conn.rollback()

            print("Fel vid skapande av verksamhet:", e)

            return render_template(
                "create_business.html",
                fel="Kunde inte skapa verksamheten"
            )

    return render_template("create_business.html")


@app.route("/skapa-tjanst", methods=["POST"])
def skapa_tjanst():

    if "user" not in session:
        return redirect(url_for("logga_in"))

    email = session["user"]

    menynamn = request.form.get("menynamn")
    beskrivning = request.form.get("beskrivning")
    pris = request.form.get("pris")

    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT verksamhet_id
            FROM public.verksamhet
            WHERE foretagare_id = (
                SELECT foretagare_id
                FROM public.foretagare
                WHERE email = %s
            )
        """, (email,))

        verksamhet_id = cursor.fetchone()[0]

        cursor.execute("""
            INSERT INTO public.meny
            (
                verksamhet_id,
                menynamn,
                beskrivning,
                pris
            )
            VALUES (%s, %s, %s, %s)
        """, (
            verksamhet_id,
            menynamn,
            beskrivning,
            pris
        ))

        conn.commit()

        return redirect(url_for("profile"))

    except Exception as e:

        conn.rollback()

        print(e)

        return "Kunde inte skapa tjänst", 500

# -------------------------------------------------------
# Admin
# -------------------------------------------------------
ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASS = os.getenv("ADMIN_PASS")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        if email == ADMIN_USER and password == ADMIN_PASS:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            return render_template("admin_login.html", fel="Felaktiga admin-uppgifter")
            
    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    
    cursor = conn.cursor()
    cursor.execute("SELECT foretagare_id, foretagsnamn, email, blockera FROM public.foretagare ORDER BY foretagare_id DESC")
    foretagare = cursor.fetchall()
    return render_template("admin_dashboard.html", foretagare=foretagare)

@app.route("/admin/blockera/<int:id>")
def blockera_foretagare(id):
    if not session.get("admin_logged_in"): return redirect(url_for("admin_login"))
    
    cursor = conn.cursor()
    cursor.execute("UPDATE public.foretagare SET blockera = NOT blockera WHERE foretagare_id = %s", (id,))
    conn.commit()
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/ta-bort/<int:id>")
def ta_bort_foretagare(id):
    if not session.get("admin_logged_in"): return redirect(url_for("admin_login"))
    
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM public.verksamhet WHERE foretagare_id = %s", (id,))
        cursor.execute("DELETE FROM public.foretagare WHERE foretagare_id = %s", (id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Fel vid radering: {e}")
        
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("home"))


# -------------------------------------------------------
# STARTA SERVERN
# -------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5001)

